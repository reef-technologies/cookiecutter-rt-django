#!/bin/bash
# Recovers the database after a failed or interrupted PostgreSQL major upgrade.
# deploy.sh runs it automatically; it is safe to run by hand and does nothing when
# there is nothing to recover. See README.md, "Upgrading PostgreSQL".
#
# It sets the old database files aside in db/data/.failed-<timestamp>, starts a fresh
# database on the configured major and restores the pre-upgrade backup that deploy.sh
# recorded. In development, where there are no backups, it starts an empty database.
# When the restore fails, the next run restores again into the same fresh database.
set -euo pipefail

cd "$(dirname "$0")/.."

db_upgrade() {
    docker compose run --rm --no-deps -T db-upgrade "$@"
}

wait_for_db() {
    # over TCP: the server started for first-boot initialisation listens only on its socket
    for _ in $(seq 120); do
        if docker compose exec -T db sh -c 'pg_isready -q -h 127.0.0.1 -U "$POSTGRES_USER"'; then
            return 0
        fi
        sleep 1
    done
    echo "ERROR: the database did not become ready" >&2
    return 1
}

state=0
db_upgrade check || state=$?
case "$state" in
    20) ;;
    1) exit 1 ;;
    *)
        echo "Nothing to recover."
        exit 0
        ;;
esac

# not in a condition: a failing docker command must stop the script, not pass for "no backup needed"
ref=$(db_upgrade backup-ref)
required=$(db_upgrade requires-backup)
if [ -z "$ref" ] && [ "$required" != no ]; then
    echo "ERROR: no pre-upgrade backup is recorded, so there is nothing to restore automatically." >&2
    echo "Restore the latest backup by hand, see README.md, \"Restoring system from backup after a catastrophical failure\"." >&2
    exit 1
fi

trap 'echo "ERROR: recovery failed; the old database files and the pre-upgrade backup are kept. Fix the cause and deploy again (or run bin/db-recover.sh) to retry. See README.md, \"Upgrading PostgreSQL\"." >&2' ERR

docker compose stop
aside=$(db_upgrade set-aside)
# without --no-deps, db would wait for db-upgrade, which refuses to run until recovery succeeds
docker compose up -d --no-deps db
wait_for_db

if [ -n "$ref" ]; then
    echo "Restoring the pre-upgrade backup $ref"
    docker compose run --rm --no-deps -T backups ./restore-db.sh "$ref"
fi
db_upgrade finish-recovery

if [ -n "$ref" ]; then
    echo "Recovered: restored $ref into a fresh database."
    echo "The old files are in db/data/$aside; the next successful deploy deletes them."
    echo "Only db is running; ./deploy.sh starts the other services."
else
    echo "Started a fresh, empty database. The old files are in db/data/$aside; delete them when you no longer need them."
    echo "Only db is running; start the other services with \`docker compose up -d\` and run the migrations."
fi
