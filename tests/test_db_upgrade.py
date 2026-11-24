"""Upgrade the bundled PostgreSQL of a generated project to the major of its `db` image, as deploy.sh does.

Needs Docker and a project generated with `deployment_type=direct`, passed in
DB_UPGRADE_TEST_PROJECT (the `test_db_upgrade` nox session sets it up).
"""

import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

PROJECT = os.environ.get("DB_UPGRADE_TEST_PROJECT")
ITEMS = [(1, "first"), (2, "second"), (3, "third")]
SEED_SQL = """
CREATE TABLE item (id int PRIMARY KEY, name text);
INSERT INTO item VALUES (1, 'first'), (2, 'second'), (3, 'third');
"""

# A deployment before the upgrade: `db` as an older image ran it, a service that uses the
# database and one that the current docker-compose.yml no longer has.
OLD_COMPOSE = """
services:
  db:
    image: {image}
    environment:
      - POSTGRES_DB=project
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=secret
      - PGDATA={mount}{cluster}
    volumes:
      - ./db/data:{mount}
  app:
    image: alpine:3.24
    command: sleep infinity
    init: true
  retired:
    image: alpine:3.24
    command: sleep infinity
    init: true
"""
# Images before 18 keep the cluster directly in db/data.
FLAT_14 = {"image": "postgres:14-alpine", "mount": "/var/lib/postgresql/data", "cluster": ""}
# 18+ images keep it in db/data/<major>/docker. The mount avoids /var/lib/postgresql, where
# the 17 image would add its own volume for the `data` subdirectory.
VERSIONED_17 = {"image": "postgres:17-alpine", "mount": "/mnt/postgresql", "cluster": "/17/docker"}

# Built once for all tests: Compose would build `backups` again under every project name.
BACKUPS_IMAGE = "db-upgrade-test-backups"
# CI hosts may not run journald, which the production compose file logs to.
TEST_OVERRIDE = f"""
x-logging: &test-logging
  driver: json-file
services:
  db: {{logging: *test-logging}}
  backups: {{logging: *test-logging, image: {BACKUPS_IMAGE}}}
"""


@unittest.skipUnless(PROJECT, "set DB_UPGRADE_TEST_PROJECT to a generated project")
class DbUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = ["docker", "build", "--quiet", "--tag", BACKUPS_IMAGE, str(Path(PROJECT) / "backups")]
        subprocess.run(build, check=True, capture_output=True)
        cls.addClassCleanup(subprocess.run, ["docker", "rmi", BACKUPS_IMAGE], capture_output=True)

    def setUp(self):
        # Compose names the project after this directory, as on servers.
        self.dir = Path(tempfile.mkdtemp(prefix="dbupgrade"))
        self.staging = f"{self.dir.name}-db-upgrade"
        project = Path(PROJECT)
        for name in ("db", "backups", "bin"):
            shutil.copytree(project / name, self.dir / name, symlinks=True)
        compose = (project / "envs/prod/docker-compose.yml").read_text()
        (self.dir / "docker-compose.yml").write_text(compose)
        (self.dir / "test.yml").write_text(TEST_OVERRIDE)
        self.target_major = re.search(r"image: postgres:(\d+)", compose).group(1)
        self.write_env()
        self.env = {
            **{key: value for key, value in os.environ.items() if key != "COMPOSE_PROJECT_NAME"},
            "COMPOSE_FILE": "docker-compose.yml:test.yml",
        }
        self.addCleanup(self.cleanup)

    def write_env(self, **overrides):
        """The project's .env template, with the credentials of the old deployment."""
        values = {
            "POSTGRES_DB": "project",
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "secret",
            "DATABASE_URL": "postgres://postgres:secret@db:5432/project",
            # as on production servers: with a DSN the backup scripts run under the Sentry hook
            "SENTRY_DSN": "https://key@sentry.invalid/1",
            **overrides,
        }
        template = (Path(PROJECT) / "envs/prod/.env.template").read_text().splitlines()
        lines = [line for line in template if line.split("=", 1)[0] not in values]
        lines += [f"{key}={value}" for key, value in values.items()]
        (self.dir / ".env").write_text("\n".join(lines) + "\n")

    def cleanup(self):
        self.run_cmd("docker", "rm", "-f", self.staging, check=False)
        for files in ("docker-compose.yml:test.yml", "old.yml"):
            if all((self.dir / file).exists() for file in files.split(":")):
                self.compose("down", "-v", "--remove-orphans", check=False, files=files)
        # the database files belong to the container's postgres user
        self.run_cmd(
            "docker", "run", "--rm", "-v", f"{self.dir}:/d", "alpine:3.24", "rm", "-rf", "/d/db/data", check=False
        )
        shutil.rmtree(self.dir)

    def run_cmd(self, *args, check=True, **env):
        result = subprocess.run(args, cwd=self.dir, env={**self.env, **env}, text=True, capture_output=True)
        if check and result.returncode:
            self.fail(f"{' '.join(args)} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
        return result

    def compose(self, *args, check=True, files=None):
        env = {"COMPOSE_FILE": files} if files else {}
        return self.run_cmd("docker", "compose", *args, check=check, **env)

    def upgrade(self, check=True):
        return self.run_cmd("bin/upgrade-db.sh", check=check)

    def psql(self, sql):
        return self.compose("exec", "-T", "db", "psql", "-U", "postgres", "-d", "project", "-Atc", sql).stdout.strip()

    def wait_for_db(self):
        for _ in range(300):
            if not self.compose("exec", "-T", "db", "pg_isready", "-q", "-h", "127.0.0.1", check=False).returncode:
                return
            time.sleep(1)
        self.fail("the database did not become ready")

    def start_old_deployment(self, layout, *extra_sql):
        (self.dir / "old.yml").write_text(OLD_COMPOSE.format(**layout))
        self.compose("up", "-d", files="old.yml")
        self.wait_for_db()
        for sql in (SEED_SQL, *extra_sql):
            self.psql(sql)

    def items(self):
        rows = self.psql("SELECT id, name FROM item ORDER BY id").splitlines()
        return [(int(id), name) for id, name in (row.split("|") for row in rows)]

    def server_major(self):
        return self.psql("SHOW server_version").split(".")[0]

    def mount_entries(self, path=""):
        """Names in db/data, which only a container may list."""
        mount = f"{self.dir}/db/data:/mount:ro"
        listing = self.run_cmd("docker", "run", "--rm", "-v", mount, "alpine:3.24", "ls", "-A", f"/mount/{path}")
        return sorted(listing.stdout.split())

    def running_services(self):
        project = f"label=com.docker.compose.project={self.dir.name}"
        service = '{{.Label "com.docker.compose.service"}}'
        return sorted(self.run_cmd("docker", "ps", "--filter", project, "--format", service).stdout.split())

    def assert_upgraded(self):
        self.assertEqual(self.server_major(), self.target_major)
        self.assertEqual(self.items(), ITEMS)
        self.assertEqual(self.mount_entries(), [".upgrade-old", self.target_major])

    def test_upgrade_from_14(self):
        self.start_old_deployment(FLAT_14)
        self.upgrade()
        self.assert_upgraded()
        self.assertIn("PG_VERSION", self.mount_entries(".upgrade-old"))
        # what used the database stays stopped until deploy.sh starts the new versions
        self.assertEqual(self.running_services(), ["db"])
        db = self.compose("ps", "-q", "db").stdout
        # the next deploy has nothing to upgrade and deletes the old files
        self.upgrade()
        self.assertEqual(self.mount_entries(), [self.target_major])
        self.assertEqual(self.compose("ps", "-q", "db").stdout, db)
        self.assertEqual(self.items(), ITEMS)

    def test_upgrade_from_major_directory(self):
        self.start_old_deployment(VERSIONED_17)
        self.upgrade()
        self.assert_upgraded()
        self.assertEqual(self.mount_entries(".upgrade-old"), ["17"])

    def test_fresh_project(self):
        self.upgrade()
        self.assertEqual(self.mount_entries(), [])
        self.compose("up", "-d", "db")
        self.wait_for_db()
        self.assertEqual(self.server_major(), self.target_major)

    def test_upgrade_ignores_host_in_database_url(self):
        # an app that keeps its data elsewhere: the upgrade must still move the bundled database only
        self.write_env(DATABASE_URL="postgres://postgres:secret@elsewhere.invalid:5432/project")
        self.start_old_deployment(FLAT_14)
        self.upgrade()
        self.assert_upgraded()

    def test_failed_restore_starts_old_deployment_again(self):
        # pg_dump does not carry roles, so the restore fails on the table that this one owns
        role_sql = "CREATE ROLE reporting; CREATE TABLE report (id int); ALTER TABLE report OWNER TO reporting;"
        self.start_old_deployment(FLAT_14, role_sql)
        running = self.running_services()
        result = self.upgrade(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Nothing was upgraded", result.stderr)
        self.wait_for_db()
        self.assertEqual(
            (self.server_major(), self.items(), self.running_services()),
            ("14", ITEMS, running),
        )
        self.assertEqual([entry for entry in self.mount_entries() if entry.startswith(".upgrade")], [])
        # db/init runs on the new cluster as well, so that is where the role belongs
        (self.dir / "db/init/02-reporting.sql").write_text("CREATE ROLE reporting;\n")
        self.upgrade()
        self.assert_upgraded()
        self.assertEqual(self.psql("SELECT tableowner FROM pg_tables WHERE tablename = 'report'"), "reporting")

    def test_killed_upgrade_is_redone(self):
        self.start_old_deployment(FLAT_14)
        upgrade = subprocess.Popen(
            ["bin/upgrade-db.sh"],
            cwd=self.dir,
            env=self.env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self.addCleanup(upgrade.wait)
        self.addCleanup(upgrade.kill)
        self.wait_for_staging()
        # a crash: nothing gets to roll back, the temporary server keeps running
        os.killpg(upgrade.pid, signal.SIGKILL)
        upgrade.wait()
        self.upgrade()
        self.assert_upgraded()
        self.assertEqual(self.run_cmd("docker", "ps", "-aq", "--filter", f"name=^{self.staging}$").stdout, "")

    def wait_for_staging(self):
        for _ in range(600):
            if self.run_cmd("docker", "ps", "-q", "--filter", f"name=^{self.staging}$").stdout:
                return
            time.sleep(1)
        self.fail("the upgrade did not start its temporary server")

    def test_interrupted_move_of_old_files_is_finished(self):
        self.start_old_deployment(FLAT_14)
        self.upgrade()
        old_files = self.mount_entries(".upgrade-old")
        # as if the upgrade had been cut off after the new cluster was in place: PG_VERSION moves last
        mount = f"{self.dir}/db/data:/mount"
        move_back = "mv /mount/.upgrade-old/PG_VERSION /mount/.upgrade-old/base /mount/"
        self.run_cmd("docker", "run", "--rm", "-v", mount, "alpine:3.24", "sh", "-c", move_back)
        self.upgrade()
        self.assert_upgraded()
        self.assertEqual(self.mount_entries(".upgrade-old"), old_files)

    def test_manual_start_of_new_version_refuses_old_data(self):
        self.start_old_deployment(FLAT_14)
        self.compose("up", "-d", "db")
        for _ in range(120):
            if "appears to be PostgreSQL data in" in self.compose("logs", "db").stdout:
                break
            time.sleep(1)
        else:
            self.fail("the new db image did not refuse the old data")
        # the refused start left an empty <major>/docker; the upgrade works once the old version runs again
        self.assertEqual(self.mount_entries(f"{self.target_major}/docker"), [])
        self.compose("up", "-d", "db", files="old.yml")
        self.wait_for_db()
        self.assertEqual(self.items(), ITEMS)
        self.upgrade()
        self.assert_upgraded()

    def test_other_database_in_cluster_is_refused(self):
        self.start_old_deployment(FLAT_14, "CREATE DATABASE analytics")
        running = self.running_services()
        result = self.upgrade(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("this server also holds: analytics", result.stderr)
        self.assertEqual((self.server_major(), self.running_services()), ("14", running))


if __name__ == "__main__":
    unittest.main()
