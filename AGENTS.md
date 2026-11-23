# Agent Guidelines

## Bumping PostgreSQL

The bundled database's PostgreSQL release is pinned in several files of `{{cookiecutter.repostory_name}}/`.
`nox -s test_postgres_versions` fails when their majors differ, or when the upgrade image is not the same release as `db`.

To move to a new release, minor or major:

1. Update these pins, each by digest:
   - `envs/prod/docker-compose.yml` and `envs/dev/docker-compose.yml`:
     the `db` image, and the `db-upgrade` image, `pgautoupgrade/pgautoupgrade` of the same release as `db`.
     Wait until pgautoupgrade publishes it; an older pgautoupgrade release may not read data written by the newest minors.
   - `backups/Dockerfile` and `bin/dbshell.sh`.
   - For a major:
     `engine_version` and `family` in `devops/tf/main/modules/database/rds.tf`.
2. Do not write manual migration steps:
   the `db-upgrade` service and `deploy.sh` upgrade existing data, see the project README's "Upgrading PostgreSQL".
3. For a major, the changelog entry is **BREAKING** and says, as does the PR description:
   schedule the deploy outside peak traffic; the app is down from the pre-upgrade backup until the upgrade and its reindex finish; rollback means reverting and restoring the pre-upgrade backup.
4. Run `nox -s test_postgres_versions test_db_upgrade`.
   The second one needs Docker and upgrades from `DB_UPGRADE_TEST_OLD_IMAGE` (in `tests/test_db_upgrade.py`).
