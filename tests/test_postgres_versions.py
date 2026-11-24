"""Every place that pins PostgreSQL uses the same major, so a version bump cannot be half done."""

import re
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1] / "{{cookiecutter.repostory_name}}"

# (file, pattern); each pattern captures the version it pins
PINS = [
    ("envs/prod/docker-compose.yml", r"^    image: postgres:(\d+\.\d+)-alpine@"),
    ("envs/prod/docker-compose.yml", r"^    image: pgautoupgrade/pgautoupgrade:(\d+\.\d+)-alpine[\d.]*@"),
    ("envs/dev/docker-compose.yml", r"^    image: mirror\.gcr\.io/postgres:(\d+\.\d+)-alpine@"),
    ("envs/dev/docker-compose.yml", r"^    image: pgautoupgrade/pgautoupgrade:(\d+\.\d+)-alpine[\d.]*@"),
    ("backups/Dockerfile", r"^FROM postgres:(\d+\.\d+)@"),
    ("bin/dbshell.sh", r" postgres:(\d+\.\d+)-alpine@"),
    ("devops/tf/main/modules/database/rds.tf", r'^  engine_version\s*= "(\d+)"'),
    ("devops/tf/main/modules/database/rds.tf", r'^  family\s*= "postgres(\d+)"'),
]


def pins():
    for file, pattern in PINS:
        found = re.findall(pattern, (PROJECT / file).read_text(), re.MULTILINE)
        yield file, pattern, found


class PostgresVersionTests(unittest.TestCase):
    def test_one_major_everywhere(self):
        majors = {}
        for file, pattern, found in pins():
            self.assertEqual(len(found), 1, f"expected one match of {pattern!r} in {file}, found {found}")
            majors[f"{file}: {pattern}"] = found[0].split(".")[0]
        self.assertEqual(len(set(majors.values())), 1, f"PostgreSQL majors differ: {majors}")

    def test_upgrade_image_matches_db_image(self):
        # pgautoupgrade has to know the catalog of the newest minors, so it must be the same release as `db`
        for compose in ("envs/prod/docker-compose.yml", "envs/dev/docker-compose.yml"):
            versions = [found[0] for file, _, found in pins() if file == compose]
            self.assertEqual(len(set(versions)), 1, f"{compose}: db and db-upgrade versions differ: {versions}")


if __name__ == "__main__":
    unittest.main()
