# Agent Guidelines

## Bumping PostgreSQL

The PostgreSQL release of the bundled database is pinned in several files of `{{cookiecutter.repostory_name}}/`.
`nox -s test_postgres_versions` fails when their majors differ.

To move to a new release, minor or major:

1. Update these pins, each by digest:
   - `envs/prod/docker-compose.yml` and `envs/dev/docker-compose.yml`:
     the `db` image, always the Alpine variant, because the files in `db/data` belong to its `postgres` user.
   - `backups/Dockerfile` and `bin/dbshell.sh`.
   - For a major:
     `engine_version` and `family` in `devops/tf/main/modules/database/rds.tf`.
2. Do not write manual migration steps:
   `deploy.sh` upgrades existing data by dump and restore, see the project README's "Upgrading PostgreSQL".
3. For a major, the changelog entry is **BREAKING** and says, as does the PR description:
   schedule the deploy outside peak traffic; the app is down for as long as the dump and the restore take; the server needs free disk space for a second copy of the database.
4. For a major, make `tests/test_db_upgrade.py` also upgrade from the major being replaced, in the `<major>/docker` layout.
5. Run `nox -s test_postgres_versions test_data_mount test_db_upgrade`.
   The last one needs Docker.
