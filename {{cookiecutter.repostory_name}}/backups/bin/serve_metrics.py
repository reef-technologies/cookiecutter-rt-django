import logging
import subprocess
import time
from argparse import ArgumentParser
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from functools import wraps
from os import environ
from pathlib import Path
from tempfile import NamedTemporaryFile

import structlog
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from prometheus_client import Gauge, Histogram, start_http_server
from structlog.contextvars import bound_contextvars

MiB = 1
GiB = 1024 * MiB

backup_size = Histogram(
    "backup_size",
    "Size of the backup",
    unit="MiB",
    buckets=(
        16 * MiB,
        64 * MiB,
        256 * MiB,
        1 * GiB,
        2 * GiB,
        4 * GiB,
        8 * GiB,
        16 * GiB,
        32 * GiB,
        64 * GiB,
        128 * GiB,
        256 * GiB,
        512 * GiB,
        1024 * GiB,
    ),
)
total_backup_size = Gauge("total_backup_size", "Total size of all backups", unit="MiB")
backup_count = Gauge("backup_count", "Number of backups")
first_backup_time = Gauge("first_backup_time", "Timestamp of the first backup")
last_backup_time = Gauge("last_backup_time", "Timestamp of the last backup")
last_backup_is_operational = Gauge("last_backup_is_operational", "Last backup is checked")

DATABASE_URL = environ["DATABASE_URL"]
LOCAL_BACKUP_PATH = Path(environ["BACKUP_LOCAL_DIR"])
LOCAL_ROTATE_KEEP_LAST = (keep_last := environ.get("BACKUP_LOCAL_ROTATE_KEEP_LAST")) and int(keep_last)

B2_BUCKET = environ.get("BACKUP_B2_BUCKET")
B2_APPLICATION_KEY_ID = environ.get("BACKUP_B2_KEY_ID")
B2_APPLICATION_KEY = environ.get("BACKUP_B2_KEY_SECRET")

log = structlog.getLogger(__name__)


def cached_method(method: Callable) -> Callable:
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        cache_key = (*args, *sorted(kwargs.items()))

        if not hasattr(self, "_cache"):
            self._cache = {}

        try:
            return self._cache[cache_key]
        except KeyError:
            self._cache[cache_key] = result = method(self, *args, **kwargs)
            return result

    return wrapper


@dataclass
class Backup:
    location: Path
    created_at: datetime
    size_bytes: int

    def __hash__(self) -> int:
        return hash(self.location)


def check_pg_restore(backup_path: Path, expected_record: str = " TABLE DATA public django_migrations ") -> bool:
    """Check whether the backup ToC can be read, and whether it contains specific record."""

    with bound_contextvars(backup_path=backup_path):
        log.debug("Testing readability of the backup")
        result = subprocess.run(["pg_restore", "-l", str(backup_path)], capture_output=True)
        if result.returncode != 0:
            log.error("Backup is not a valid PostgreSQL dump", result=result)
            return False

        with bound_contextvars(expected_record=expected_record):
            log.debug("Checking if backup contains expected record")
            if expected_record not in result.stdout.decode():
                log.error("Backup is missing expected record", result=result)
                return False

            return True


class BackupManager:
    def iter_backups(self) -> Iterator[Backup]:
        raise NotImplementedError

    def check_is_operational(self, backup: Backup) -> bool:
        raise NotImplementedError


@dataclass
class LocalBackupManager(BackupManager):
    backups_path: Path
    extension: str = "zstd"

    def iter_backups(self) -> Iterator[Backup]:
        for backup_path in sorted(self.backups_path.glob(f"*.{self.extension}")):
            stat = backup_path.stat()
            yield Backup(
                location=backup_path,
                created_at=datetime.fromtimestamp(stat.st_ctime, tz=UTC),
                size_bytes=stat.st_size,
            )

    @cached_method
    def check_is_operational(self, backup: Backup) -> bool:
        return check_pg_restore(backup.location)


@dataclass
class B2BackupManager(BackupManager):
    bucket_name: str
    application_key_id: str
    application_key: str

    b2: B2Api = field(default_factory=lambda: B2Api(InMemoryAccountInfo()))
    integrity_check_download_bytes: int = 1024 * 1024 * 10

    def __post_init__(self):
        log.debug("Authorizing B2 account")
        self.b2.authorize_account("production", self.application_key_id, self.application_key)

    def iter_backups(self) -> Iterator[Backup]:
        bucket = self.b2.get_bucket_by_name(B2_BUCKET)
        for file_version, _ in bucket.ls():
            yield Backup(
                location=Path(file_version.file_name),
                created_at=datetime.fromtimestamp(file_version.upload_timestamp / 1000, tz=UTC),
                size_bytes=file_version.size,
            )

    @cached_method
    def check_is_operational(self, backup: Backup) -> bool:
        """
        Download only head of the backup file, and use it to retrieve DB ToC.
        N.B.: If it fails, switch to streaming: curl -s <URL_TO_BACKUP> | pg_restore -l
        """

        log.debug("Downloading a part of the backup for integrity check", backup=backup)
        bucket = self.b2.get_bucket_by_name(self.bucket_name)
        downloaded_file = bucket.download_file_by_name(
            str(backup.location), range_=(0, self.integrity_check_download_bytes)
        )
        with NamedTemporaryFile() as temp_file:
            downloaded_file.save(temp_file)
            return check_pg_restore(temp_file.name)


def update_metrics() -> None:
    if B2_BUCKET:
        log.debug("Using B2 backup manager")
        manager = B2BackupManager(
            application_key_id=B2_APPLICATION_KEY_ID,
            application_key=B2_APPLICATION_KEY,
            bucket_name=B2_BUCKET,
        )
    else:
        log.debug("Using local backup manager")
        manager = LocalBackupManager(LOCAL_BACKUP_PATH)

    backups = manager.iter_backups()
    first_backup, last_backup = None, None
    num_backups = 0
    total_size = 0
    for num_backups, backup in enumerate(backups, start=1):  # noqa: B007
        log.debug("Processing backup", backup=backup)
        size_mib = backup.size_bytes / 1024 / 1024
        backup_size.observe(size_mib)
        total_size += size_mib

        if not first_backup or first_backup.created_at > backup.created_at:
            first_backup = backup

        if not last_backup or last_backup.created_at < backup.created_at:
            last_backup = backup

    backup_count.set(num_backups)
    total_backup_size.set(total_size)

    if first_backup:
        first_backup_time.set(first_backup.created_at.timestamp())

    if last_backup:
        last_backup_time.set(last_backup.created_at.timestamp())
        log.debug("Checking newest backup", last_backup=last_backup)
        is_operational = manager.check_is_operational(last_backup)
        last_backup_is_operational.set(is_operational)
    else:
        log.debug("No backups found")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--interval", type=int, default=timedelta(minutes=10).total_seconds(), help="Refresh interval (s)"
    )
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    args = parser.parse_args()

    level = getattr(logging, args.log_level.upper())
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(level))

    log.info("Starting metrics server", port=args.port, interval=args.interval)
    start_http_server(args.port)
    while True:
        log.debug("Updating metrics")
        update_metrics()
        time.sleep(args.interval)
