"""Upgrade a project's bundled PostgreSQL from 14 to the configured major, as deploy.sh does.

Needs Docker and a project generated with `deployment_type=direct`, passed in
DB_UPGRADE_TEST_PROJECT (the `test_db_upgrade` nox session sets it up).
"""

import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

PROJECT = os.environ.get("DB_UPGRADE_TEST_PROJECT")
OLD_IMAGE = os.environ.get("DB_UPGRADE_TEST_OLD_IMAGE", "postgres:14-alpine")
ROWS = 1000
SEED_SQL = (
    "CREATE TABLE item (id int PRIMARY KEY, name text);"
    "INSERT INTO item SELECT g, 'item ' || g FROM generate_series(1, 1000) g;"
)
# pg_upgrade refuses user columns of reg* types other than regclass, regrole and regtype
UNUPGRADABLE_SQL = "CREATE TABLE fn (f regproc); INSERT INTO fn VALUES ('now');"

# The deployment before the upgrade: PostgreSQL 14 with the data directory mounted the pre-18 way.
OLD_COMPOSE = f"""
services:
  db:
    image: {OLD_IMAGE}
    environment:
      - POSTGRES_DB=project
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=secret
    volumes:
      - ./db/data:/var/lib/postgresql/data
"""

# A service removed from docker-compose.yml whose container still runs, as after a template update.
RETIRED_COMPOSE = """
services:
  retired:
    image: alpine:3.24
    command: sleep infinity
    init: true
"""

# CI hosts may not run journald, which the production compose file logs to.
TEST_OVERRIDE = """
x-logging: &test-logging
  driver: json-file
services:
  db-upgrade: {logging: *test-logging}
  db: {logging: *test-logging}
  backups: {logging: *test-logging}
"""


@unittest.skipUnless(PROJECT, "set DB_UPGRADE_TEST_PROJECT to a generated project")
class DbUpgradeTests(unittest.TestCase):
    def setUp(self):
        # Compose names the project after this directory, as on servers: with an explicit name
        # (`-p`, COMPOSE_PROJECT_NAME), `docker compose stop` accepts services removed from the file.
        self.dir = Path(tempfile.mkdtemp(prefix="dbupgrade"))
        project = Path(PROJECT)
        for name in ("db", "backups", "bin"):
            shutil.copytree(project / name, self.dir / name, symlinks=True)
        shutil.copy(project / "envs/prod/docker-compose.yml", self.dir / "docker-compose.yml")
        shutil.copy(project / "envs/dev/docker-compose.yml", self.dir / "dev.yml")
        self.write_env(project / "envs/prod/.env.template")
        (self.dir / "old.yml").write_text(OLD_COMPOSE)
        (self.dir / "test.yml").write_text(TEST_OVERRIDE)
        self.env = {
            **{key: value for key, value in os.environ.items() if key != "COMPOSE_PROJECT_NAME"},
            "COMPOSE_FILE": "docker-compose.yml:test.yml",
        }
        self.addCleanup(self.cleanup)

    def write_env(self, template, **overrides):
        """The project's .env template, with the database credentials the old deployment uses."""
        overrides = {
            "POSTGRES_DB": "project",
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "secret",
            "DATABASE_URL": "postgres://postgres:secret@db:5432/project",
            **overrides,
        }
        lines = [line for line in template.read_text().splitlines() if line.split("=", 1)[0] not in overrides]
        lines += [f"{key}={value}" for key, value in overrides.items()]
        (self.dir / ".env").write_text("\n".join(lines) + "\n")

    def cleanup(self):
        for files in ("docker-compose.yml:test.yml", "old.yml", "dev.yml"):
            self.run_cmd("docker", "compose", "down", "-v", "--remove-orphans", check=False, COMPOSE_FILE=files)
        # the database files belong to the container's postgres user
        self.run_cmd(
            "docker", "run", "--rm", "-v", f"{self.dir}:/d", "alpine:3.24", "rm", "-rf", "/d/db/data", check=False
        )
        shutil.rmtree(self.dir)

    def run_cmd(self, *args, check=True, input=None, **env):
        result = subprocess.run(
            args, cwd=self.dir, env={**self.env, **env}, text=True, capture_output=True, input=input
        )
        if check and result.returncode:
            self.fail(f"{' '.join(args)} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
        return result

    def compose(self, *args, **kwargs):
        return self.run_cmd("docker", "compose", *args, **kwargs)

    def db_upgrade(self, *args, check=True):
        return self.compose("run", "--rm", "--no-deps", "-T", "db-upgrade", *args, check=check)

    def deploy_db(self, check=True):
        return self.run_cmd("bin/deploy-db.sh", check=check)

    def psql(self, sql, files=None):
        files = {"COMPOSE_FILE": files} if files else {}
        return self.compose(
            "exec", "-T", "db", "psql", "-U", "postgres", "-d", "project", "-Atc", sql, **files
        ).stdout.strip()

    def wait_for_db(self, files=None):
        files = {"COMPOSE_FILE": files} if files else {}
        for _ in range(120):
            if not self.compose(
                "exec", "-T", "db", "pg_isready", "-q", "-h", "127.0.0.1", check=False, **files
            ).returncode:
                return
            time.sleep(1)
        self.fail("database did not become ready")

    def data_files(self, path=""):
        return self.db_upgrade_shell(f"ls -A /var/lib/postgresql/{path}").split()

    def db_upgrade_shell(self, script):
        return self.compose("run", "--rm", "--no-deps", "-T", "--entrypoint", "sh", "db-upgrade", "-c", script).stdout

    def backups_shell(self, script):
        return self.compose("run", "--rm", "--no-deps", "-T", "--entrypoint", "sh", "backups", "-c", script).stdout

    def target_major(self):
        return self.db_upgrade_shell("echo $PG_MAJOR").strip()

    def set_aside_dirs(self):
        return [name for name in self.data_files() if name.startswith(".failed-")]

    def record_backup(self):
        """What deploy-db.sh does before an upgrade: back up the old server, stop it and record the backup."""
        ref = self.compose("run", "--rm", "--no-deps", "-T", "backups", "./backup-db-ref.sh").stdout.splitlines()[-1]
        self.compose("stop", "db", COMPOSE_FILE="old.yml")
        self.db_upgrade("mark-backup", ref)
        return ref

    def start_old_deployment(self, *extra_sql):
        self.compose("up", "-d", "db", COMPOSE_FILE="old.yml")
        self.wait_for_db("old.yml")
        for sql in (SEED_SQL, *extra_sql):
            self.psql(sql, "old.yml")

    def assert_upgraded(self, files=None):
        self.wait_for_db(files)
        major = self.target_major()
        self.assertTrue(self.psql("SHOW server_version", files).startswith(f"{major}."))
        self.assertEqual(self.psql("SELECT count(*), max(name) FROM item", files), f"{ROWS}|item 999")
        self.assertIn("PG_VERSION", self.data_files(f"{major}/docker"))
        self.assertNotIn("PG_VERSION", self.data_files())
        self.assertEqual(self.db_upgrade("check").returncode, 0)

    def test_upgrade_from_14(self):
        self.start_old_deployment()
        self.deploy_db()
        self.assert_upgraded()
        # upgraded in place, not recovered from the backup
        self.assertFalse(self.set_aside_dirs())
        # starting again is a no-op
        self.compose("up", "-d", "db")
        self.deploy_db()
        self.assert_upgraded()
        self.assertEqual(self.db_upgrade("backup-ref").stdout, "")

    def test_dev_upgrade_on_compose_up(self):
        self.start_old_deployment()
        self.compose("stop", "db", COMPOSE_FILE="old.yml")
        self.write_env(Path(PROJECT) / "envs/dev/.env.template", POSTGRES_PORT="0")
        # development upgrades without a backup
        self.compose("up", "-d", "db", COMPOSE_FILE="dev.yml")
        self.assert_upgraded("dev.yml")

    def test_fresh_project(self):
        self.deploy_db()
        self.wait_for_db()
        self.assertEqual(self.psql("SELECT 1"), "1")
        self.assertEqual(self.db_upgrade("check").stdout.strip(), "current")

    def test_plain_up_refuses_without_backup(self):
        self.start_old_deployment()
        self.compose("stop", "db", COMPOSE_FILE="old.yml")
        result = self.compose("up", "-d", "db", check=False)
        self.assertNotEqual(result.returncode, 0)
        logs = self.compose("logs", "db-upgrade").stdout
        self.assertIn("no pre-upgrade backup is recorded", logs)
        self.assertEqual(self.db_upgrade_shell("cat /var/lib/postgresql/PG_VERSION").strip(), "14")

    def test_two_clusters_refused(self):
        self.db_upgrade_shell(
            "echo 14 > /var/lib/postgresql/PG_VERSION && mkdir -p /var/lib/postgresql/17/docker"
            " && echo 17 > /var/lib/postgresql/17/docker/PG_VERSION"
        )
        result = self.db_upgrade("check", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("more than one cluster", result.stderr)
        self.assertEqual(self.data_files("17/docker"), ["PG_VERSION"])
        self.assertIn("PG_VERSION", self.data_files())

    def test_failed_upgrade_falls_back_to_restore(self):
        self.start_old_deployment(UNUPGRADABLE_SQL)
        self.deploy_db()
        self.assert_upgraded()
        self.assertEqual(self.psql("SELECT f FROM fn"), "now")
        aside = self.set_aside_dirs()
        self.assertEqual(len(aside), 1)
        self.db_upgrade("cleanup", "99991231T000000Z")
        self.assertFalse(self.set_aside_dirs())

    def test_recovery_refuses_without_disk_space(self):
        self.start_old_deployment(UNUPGRADABLE_SQL)
        with (self.dir / ".env").open("a") as env:
            env.write("DB_UPGRADE_RESERVE_MB=100000000\n")
        result = self.deploy_db(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not enough disk space", result.stderr)
        # nothing was set aside and the backup is still recorded for the next attempt
        self.assertFalse(self.set_aside_dirs())
        self.assertTrue(self.db_upgrade("backup-ref").stdout.strip())
        self.assertEqual(self.db_upgrade("check", check=False).returncode, 20)

    def test_plain_up_refuses_stale_backup(self):
        self.start_old_deployment()
        self.record_backup()
        # the old version runs again and gets writes the backup does not have
        self.compose("up", "-d", "db", COMPOSE_FILE="old.yml")
        self.wait_for_db("old.yml")
        self.psql("INSERT INTO item VALUES (1001, 'after the backup')", "old.yml")
        self.compose("stop", "db", COMPOSE_FILE="old.yml")
        self.assertNotEqual(self.compose("up", "-d", "db", check=False).returncode, 0)
        self.assertIn("no pre-upgrade backup is recorded", self.compose("logs", "db-upgrade").stdout)
        result = self.deploy_db(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no pre-upgrade backup is recorded", result.stderr)
        self.assertEqual(self.db_upgrade_shell("cat /var/lib/postgresql/PG_VERSION").strip(), "14")

    def test_upgrade_continues_after_failure_before_lock(self):
        self.start_old_deployment()
        self.record_backup()
        # pgautoupgrade rejects POSTGRES_PASSWORD together with POSTGRES_PASSWORD_FILE before it changes anything
        result = self.compose(
            "run", "--rm", "--no-deps", "-T", "-e", "POSTGRES_PASSWORD_FILE=/etc/hostname", "db-upgrade", check=False
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("without leaving a partial upgrade behind", result.stderr)
        # the cluster was already moved, so the old version could not start on it
        self.assertIn("PG_VERSION", self.data_files(f"{self.target_major()}/docker"))
        self.assertEqual(self.db_upgrade("check", check=False).returncode, 10)
        self.deploy_db()
        self.assert_upgraded()
        self.assertFalse(self.set_aside_dirs())

    def test_failed_restore_is_retried(self):
        self.start_old_deployment(UNUPGRADABLE_SQL)
        ref = self.record_backup()
        self.assertNotEqual(self.compose("up", "-d", "db", check=False).returncode, 0)
        self.assertEqual(self.db_upgrade("check", check=False).returncode, 20)
        self.backups_shell(f"mv {ref} {ref}.hidden")
        self.assertNotEqual(self.run_cmd("bin/db-recover.sh", check=False).returncode, 0)
        # the fresh database started for the restore is not taken for the recovered one
        self.assertEqual(self.db_upgrade("check", check=False).returncode, 20)
        self.db_upgrade("cleanup", "99991231T000000Z")
        self.assertEqual(len(self.set_aside_dirs()), 1)
        self.backups_shell(f"mv {ref}.hidden {ref}")
        self.deploy_db()
        self.assert_upgraded()
        self.assertEqual(self.psql("SELECT f FROM fn"), "now")
        self.assertEqual(len(self.set_aside_dirs()), 1)

    def test_recovery_refuses_without_backup(self):
        self.start_old_deployment()
        self.compose("stop", "db", COMPOSE_FILE="old.yml")
        # an interrupted upgrade, but no backup was recorded
        self.db_upgrade_shell("touch /var/lib/postgresql/upgrade_in_progress.lock")
        self.assertEqual(self.db_upgrade("check", check=False).returncode, 20)
        result = self.db_upgrade("set-aside", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no pre-upgrade backup is recorded", result.stderr)
        result = self.run_cmd("bin/db-recover.sh", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no pre-upgrade backup is recorded", result.stderr)
        self.assertIn("PG_VERSION", self.data_files())
        self.assertFalse(self.set_aside_dirs())

    def test_container_of_removed_service_is_stopped(self):
        (self.dir / "retired.yml").write_text(RETIRED_COMPOSE)
        self.compose("up", "-d", "retired", COMPOSE_FILE="retired.yml")
        self.start_old_deployment()
        self.deploy_db()
        self.assert_upgraded()
        retired = f"{self.dir.name}-retired-1"
        self.assertEqual(self.run_cmd("docker", "inspect", "-f", "{{.State.Running}}", retired).stdout.strip(), "false")

    def wait_for_upgrade_start(self):
        container = f"{self.dir.name}-db-upgrade-1"
        for _ in range(600):
            logs = self.run_cmd("docker", "logs", container, check=False)
            if "Running pg_upgrade command" in logs.stdout + logs.stderr:
                return container
            time.sleep(0.1)
        self.fail("the upgrade did not start")

    def test_stop_signal_does_not_interrupt_upgrade(self):
        self.start_old_deployment()
        deploy = subprocess.Popen(
            ["bin/deploy-db.sh"], cwd=self.dir, env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.addCleanup(deploy.kill)
        container = self.wait_for_upgrade_start()
        # what `docker compose stop` sends first
        self.run_cmd("docker", "kill", "--signal", "TERM", container)
        self.assertEqual(deploy.wait(timeout=600), 0)
        self.assertEqual(self.run_cmd("docker", "inspect", "-f", "{{.State.ExitCode}}", container).stdout.strip(), "0")
        self.assert_upgraded()
        self.assertFalse(self.set_aside_dirs())

    def test_interrupted_upgrade_recovers_on_next_deploy(self):
        self.start_old_deployment()
        deploy = subprocess.Popen(
            ["bin/deploy-db.sh"], cwd=self.dir, env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.addCleanup(deploy.kill)
        container = self.wait_for_upgrade_start()
        # a crash or power loss: nothing gets to clean up
        deploy.kill()
        deploy.wait()
        self.run_cmd("docker", "kill", container)
        self.assertEqual(self.db_upgrade("check", check=False).returncode, 20)
        self.deploy_db()
        self.assert_upgraded()


if __name__ == "__main__":
    unittest.main()
