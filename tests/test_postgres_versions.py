"""Every place that pins PostgreSQL uses the same major, so a version bump cannot be half done."""

import re
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1] / "{{cookiecutter.repostory_name}}"

# (file, pattern capturing the pinned version). `db` stays on Alpine: its postgres user owns
# db/data, and the Debian images run PostgreSQL under another user ID.
PINS = [
    ("envs/prod/docker-compose.yml", r"^    image: postgres:(\d+\.\d+)-alpine@"),
    ("envs/dev/docker-compose.yml", r"^    image: mirror\.gcr\.io/postgres:(\d+\.\d+)-alpine@"),
    ("backups/Dockerfile", r"^FROM postgres:(\d+\.\d+)@"),
    ("bin/dbshell.sh", r" postgres:(\d+\.\d+)-alpine@"),
    ("devops/tf/main/modules/database/rds.tf", r'^  engine_version\s*= "(\d+)"'),
    ("devops/tf/main/modules/database/rds.tf", r'^  family\s*= "postgres(\d+)"'),
]


class PostgresVersionTests(unittest.TestCase):
    def test_one_major_everywhere(self):
        majors = {}
        for file, pattern in PINS:
            found = re.findall(pattern, (PROJECT / file).read_text(), re.MULTILINE)
            self.assertEqual(len(found), 1, f"expected one match of {pattern!r} in {file}, found {found}")
            majors[f"{file}: {pattern}"] = found[0].split(".")[0]
        expected_major = majors[f"{PINS[0][0]}: {PINS[0][1]}"]
        self.assertEqual(majors, dict.fromkeys(majors, expected_major))


if __name__ == "__main__":
    unittest.main()
