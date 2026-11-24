"""Check how db/data-mount.sh classifies and rearranges the PostgreSQL data mount.

The script runs on a temporary directory, so these tests need neither Docker nor PostgreSQL.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "{{cookiecutter.repostory_name}}"
    / "db"
    / "{% if cookiecutter.deployment_type == 'direct' %}data-mount.sh{% endif %}"
)
TARGET_MAJOR = "18"
# where the pre-18 images and the 18+ images keep a cluster, relative to the mount
FLAT = "."
TARGET = f"{TARGET_MAJOR}/docker"
NEW = ".upgrade-new"
OLD = ".upgrade-old"


def cluster(path, major):
    """The files that stand in for a cluster of `major` at `path`, as `tree` reports them."""
    prefix = "" if path == FLAT else f"{path}/"
    return {f"{prefix}PG_VERSION": f"{major}\n", f"{prefix}base/1": f"data of {major}"}


class DataMountTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.mount = Path(directory.name)

    def write(self, files):
        for path, content in files.items():
            target = self.mount / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)

    def tree(self):
        """Every file in the mount with its content."""
        return {
            str(path.relative_to(self.mount)): path.read_text()
            for path in sorted(self.mount.rglob("*"))
            if path.is_file()
        }

    def run_script(self, command):
        return subprocess.run(
            ["bash", str(SCRIPT), command],
            env={**os.environ, "DATA_MOUNT": str(self.mount), "PG_MAJOR": TARGET_MAJOR},
            text=True,
            capture_output=True,
        )

    def assert_refused(self, command, message, files):
        """The command fails with `message` and leaves the mount as it was."""
        result = self.run_script(command)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(message, result.stderr)
        self.assertEqual(self.tree(), files)

    def test_state(self):
        layouts = {
            "fresh": {},
            "pending 14": cluster(FLAT, "14"),
            "pending 17": cluster("17/docker", "17"),
            "current": cluster(TARGET, "18"),
            "promoting": {**cluster(TARGET, "18"), **cluster(FLAT, "14")},
        }
        for state, files in layouts.items():
            with self.subTest(state=state):
                self.setUp()
                self.write(files)
                result = self.run_script("state")
                self.assertEqual((result.returncode, result.stdout), (0, f"{state}\n"), result.stderr)

    def test_state_promoting_with_old_cluster_in_major_directory(self):
        self.write({**cluster(TARGET, "18"), **cluster("17/docker", "17")})
        self.assertEqual(self.run_script("state").stdout, "promoting\n")

    def test_state_ignores_directory_left_by_refused_start(self):
        self.write(cluster(FLAT, "14"))
        (self.mount / TARGET).mkdir(parents=True)
        self.assertEqual(self.run_script("state").stdout, "pending 14\n")

    def test_state_ignores_files_that_are_not_a_cluster(self):
        self.write({**cluster(TARGET, "18"), "lost+found/note": "not PostgreSQL"})
        self.assertEqual(self.run_script("state").stdout, "current\n")

    def test_state_refuses_two_old_clusters(self):
        files = {**cluster(FLAT, "14"), **cluster("17/docker", "17")}
        self.write(files)
        self.assert_refused("state", "more than one PostgreSQL cluster", files)

    def test_state_refuses_newer_cluster(self):
        files = cluster("19/docker", "19")
        self.write(files)
        self.assert_refused("state", "downgrades are not supported", files)

    def test_state_refuses_mount_with_only_upgrade_leftovers(self):
        for leftover in (NEW, OLD):
            with self.subTest(leftover=leftover):
                self.setUp()
                files = cluster(leftover, "14")
                self.write(files)
                self.assert_refused("state", "holds no PostgreSQL cluster in place", files)

    def test_clean_deletes_upgrade_directories_only(self):
        layouts = {
            "current": cluster(TARGET, "18"),
            "pending": cluster(FLAT, "14"),
        }
        for state, files in layouts.items():
            with self.subTest(state=state):
                self.setUp()
                self.write({**files, **cluster(NEW, "18"), **cluster(OLD, "13")})
                result = self.run_script("clean")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.tree(), files)

    def test_clean_refuses_while_old_cluster_is_not_set_aside(self):
        files = {**cluster(TARGET, "18"), "PG_VERSION": "14\n", f"{OLD}/base/1": "data of 14"}
        self.write(files)
        self.assert_refused("clean", "not set aside yet", files)

    def test_promote_cluster_kept_directly_in_mount(self):
        self.write({**cluster(FLAT, "14"), **cluster(NEW, "18")})
        result = self.run_script("promote")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tree(), {**cluster(TARGET, "18"), **cluster(OLD, "14")})

    def test_promote_cluster_kept_in_major_directory(self):
        self.write({**cluster("17/docker", "17"), **cluster(NEW, "18"), "lost+found/note": "not PostgreSQL"})
        result = self.run_script("promote")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.tree(),
            {**cluster(TARGET, "18"), **cluster(f"{OLD}/17/docker", "17"), "lost+found/note": "not PostgreSQL"},
        )

    def test_promote_replaces_directory_left_by_refused_start(self):
        self.write({**cluster(FLAT, "14"), **cluster(NEW, "18")})
        (self.mount / TARGET).mkdir(parents=True)
        result = self.run_script("promote")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tree(), {**cluster(TARGET, "18"), **cluster(OLD, "14")})

    def test_promote_finishes_interrupted_move_of_old_cluster(self):
        self.write({**cluster(TARGET, "18"), "PG_VERSION": "14\n", f"{OLD}/base/1": "data of 14"})
        self.assertEqual(self.run_script("state").stdout, "promoting\n")
        result = self.run_script("promote")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tree(), {**cluster(TARGET, "18"), **cluster(OLD, "14")})
        self.assertEqual(self.run_script("state").stdout, "current\n")

    def test_promote_refuses_occupied_target(self):
        files = {**cluster(FLAT, "14"), **cluster(NEW, "18"), f"{TARGET}/base/1": "not a whole cluster"}
        self.write(files)
        self.assert_refused("promote", "is not empty", files)

    def test_promote_refuses_missing_or_wrong_new_cluster(self):
        for new in ({}, cluster(NEW, "17")):
            with self.subTest(new=new):
                self.setUp()
                files = {**cluster(FLAT, "14"), **new}
                self.write(files)
                self.assert_refused("promote", "holds no PostgreSQL 18 cluster", files)

    def test_promote_refuses_cluster_that_is_not_shut_down(self):
        for running in (FLAT, NEW):
            with self.subTest(running=running):
                self.setUp()
                files = {**cluster(FLAT, "14"), **cluster(NEW, "18"), f"{running}/postmaster.pid": "1\n"}
                self.write(files)
                self.assert_refused("promote", "postmaster.pid exists", self.tree())


if __name__ == "__main__":
    unittest.main()
