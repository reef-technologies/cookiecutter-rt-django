#!/bin/bash
# Runs in the `db-upgrade` service (pgautoupgrade image) before `db` starts.
# Finds the cluster under /var/lib/postgresql, moves it to the directory the
# configured major expects and upgrades it in place. See README.md, "Upgrading PostgreSQL".
#
# Commands (default: run):
#   run                upgrade if needed; exit 0 when `db` can start
#   check              report the state: 0 nothing to do, 10 upgrade pending,
#                      20 recovery needed, 1 blocked (see message)
#   mark-backup REF    record REF as the pre-upgrade backup of the stopped cluster
#   has-backup         exit 0 if an upgrade is pending and its pre-upgrade backup is recorded
#   backup-ref         print the recorded pre-upgrade backup (nothing if none)
#   requires-backup    print `yes` if this environment upgrades only with a recorded backup, else `no`
#   set-aside          move all database files to db/data/.failed-<timestamp> (prints the name)
#   finish-recovery    forget the recorded backup and the set-aside step once recovery succeeded
#   cleanup STAMP      delete set-aside directories older than STAMP (format of `date -u +%Y%m%dT%H%M%SZ`)
set -euo pipefail

ROOT=/var/lib/postgresql
TARGET_MAJOR="${PG_MAJOR:?}"
TARGET_DIR="${PGDATA:?}"
STATE_DIR="$ROOT/.upgrade"
BACKUP_MARKER="$STATE_DIR/backup"
RELOCATION_MARKER="$STATE_DIR/relocating"
# Exists from set-aside until recovery succeeded, so the fresh cluster started in between
# never passes for the recovered database.
RECOVERY_MARKER="$STATE_DIR/recovering"
# pgautoupgrade leaves these in the cluster directory when an upgrade did not finish
LEFTOVERS=(upgrade_in_progress.lock old new)

log() { echo "db-upgrade: $*" >&2; }
die() { log "ERROR: $*"; exit 1; }

# A cluster is a directory with PG_VERSION: the pre-18 layout keeps it directly in the
# mount, 18+ in <major>/docker.
find_clusters() {
    if [ -s "$ROOT/PG_VERSION" ]; then
        echo "$ROOT"
    fi
    local dir
    for dir in "$ROOT"/[0-9]*/docker; do
        if [ -s "$dir/PG_VERSION" ]; then
            echo "$dir"
        fi
    done
}

find_leftovers() {
    local dir name
    for dir in "$ROOT" "$ROOT"/[0-9]*/docker; do
        for name in "${LEFTOVERS[@]}"; do
            if [ -e "$dir/$name" ]; then
                echo "$dir/$name"
            fi
        done
    done
}

# Everything in the mount except our dot-directories (state and set-aside data)
all_entries() {
    local entry
    for entry in "$ROOT"/*; do
        if [ -e "$entry" ]; then
            echo "$entry"
        fi
    done
}

# Entries of a pre-18 cluster kept directly in the mount: all but the <major> directories
legacy_entries() {
    local entry
    all_entries | while read -r entry; do
        case "$(basename "$entry")" in
            *[!0-9]*) echo "$entry" ;;
        esac
    done
}

# Moves the cluster at $1 to $TARGET_DIR. Each step is a rename on the same filesystem,
# and the marker lets the next run finish a move that was interrupted.
relocate() {
    local source=$1
    mkdir -p "$STATE_DIR"
    echo "$source" > "$RELOCATION_MARKER"
    sync "$RELOCATION_MARKER"
    finish_relocation
}

finish_relocation() {
    [ -f "$RELOCATION_MARKER" ] || return 0
    local source
    source=$(cat "$RELOCATION_MARKER")
    log "moving the cluster from $source to $TARGET_DIR"
    if [ "$source" = "$ROOT" ]; then
        install -d -m 0700 -o postgres -g postgres "$TARGET_DIR"
        legacy_entries | while read -r entry; do
            mv "$entry" "$TARGET_DIR/"
        done
    elif [ -d "$source" ]; then
        if [ -d "$TARGET_DIR" ]; then
            rmdir "$TARGET_DIR" || die "$TARGET_DIR is not empty, cannot move $source there"
        fi
        mkdir -p "$(dirname "$TARGET_DIR")"
        mv "$source" "$TARGET_DIR"
        rmdir "$(dirname "$source")" 2>/dev/null || true
    fi
    sync "$TARGET_DIR"
    rm -f "$RELOCATION_MARKER"
}

# The recovery marker names the set-aside directory and the phase: `moving` while the
# database files are being moved there, `restoring` once they all are.
write_recovery_marker() {
    mkdir -p "$STATE_DIR"
    printf 'aside=%s\nphase=%s\n' "$1" "$2" > "$RECOVERY_MARKER.tmp"
    mv "$RECOVERY_MARKER.tmp" "$RECOVERY_MARKER"
    sync "$RECOVERY_MARKER"
}

recovery_field() {
    sed -n "s/^$1=//p" "$RECOVERY_MARKER"
}

# Sets STATE (fresh, current, relocate, pending, recover) and CLUSTER, CLUSTER_MAJOR.
# Dies when the state is one we must not act on.
inspect() {
    finish_relocation
    CLUSTER=
    CLUSTER_MAJOR=
    local leftovers clusters count
    if [ -f "$RECOVERY_MARKER" ]; then
        log "a recovery did not finish; the old database files are in db/data/$(recovery_field aside)"
        STATE=recover
        return
    fi
    leftovers=$(find_leftovers)
    if [ -n "$leftovers" ]; then
        log "an earlier upgrade did not finish, found: $(echo "$leftovers" | tr '\n' ' ')"
        STATE=recover
        return
    fi
    clusters=$(find_clusters)
    count=$(echo -n "$clusters" | grep -c '^' || true)
    if [ "$count" -eq 0 ]; then
        STATE=fresh
        return
    fi
    if [ "$count" -gt 1 ]; then
        die "found more than one cluster, refusing to guess which one is in use: $(echo "$clusters" | tr '\n' ' ')"
    fi
    CLUSTER=$clusters
    CLUSTER_MAJOR=$(cat "$CLUSTER/PG_VERSION")
    if [ "${CLUSTER_MAJOR%%.*}" -gt "$TARGET_MAJOR" ]; then
        die "the cluster in $CLUSTER is PostgreSQL $CLUSTER_MAJOR, newer than the configured $TARGET_MAJOR; downgrades are not supported"
    fi
    if [ "$CLUSTER_MAJOR" = "$TARGET_MAJOR" ]; then
        if [ "$CLUSTER" = "$TARGET_DIR" ]; then
            STATE=current
        else
            STATE=relocate
        fi
    else
        STATE=pending
    fi
}

require_stopped() {
    if [ -e "$CLUSTER/postmaster.pid" ]; then
        die "$CLUSTER/postmaster.pid exists: the database server is running or was not shut down cleanly. Stop it first (docker compose stop db). If it is not running, start the old version once and stop it cleanly."
    fi
}

# pg_control changes whenever a server starts or checkpoints, so its checksum identifies
# the cluster files exactly as they were when the backup was recorded.
control_checksum() {
    sha256sum "$CLUSTER/global/pg_control" | cut -d ' ' -f 1
}

backup_marker_matches() {
    [ -f "$BACKUP_MARKER" ] \
        && [ "$(sed -n 's/^from=//p' "$BACKUP_MARKER")" = "$CLUSTER_MAJOR" ] \
        && [ "$(sed -n 's/^control=//p' "$BACKUP_MARKER")" = "$(control_checksum)" ]
}

cmd_run() {
    inspect
    case "$STATE" in
        fresh | current)
            return 0
            ;;
        recover)
            die "run bin/db-recover.sh (deploy.sh runs it automatically)"
            ;;
        relocate)
            require_stopped
            relocate "$CLUSTER"
            return 0
            ;;
    esac
    require_stopped
    if [ "${DB_UPGRADE_REQUIRE_BACKUP:-}" = 1 ] && ! backup_marker_matches; then
        die "PostgreSQL $CLUSTER_MAJOR → $TARGET_MAJOR upgrade pending, but no pre-upgrade backup is recorded for the current database files. Run ./deploy.sh, which takes one and then upgrades."
    fi
    log "upgrading PostgreSQL $CLUSTER_MAJOR → $TARGET_MAJOR; do not interrupt"
    # an earlier attempt that failed before pgautoupgrade changed anything has moved it already
    if [ "$CLUSTER" != "$TARGET_DIR" ]; then
        relocate "$CLUSTER"
    fi
    # Ignored signals stay ignored in pgautoupgrade: `docker compose stop` waits for
    # the upgrade (up to stop_grace_period) instead of interrupting it.
    trap '' TERM INT HUP
    local status=0
    PGAUTO_ONESHOT=yes /usr/local/bin/docker-entrypoint.sh postgres || status=$?
    if [ -n "$(find_leftovers)" ]; then
        die "pgautoupgrade failed (exit $status) during the upgrade; run bin/db-recover.sh (deploy.sh runs it automatically)"
    fi
    if [ "$status" -ne 0 ] || [ "$(cat "$TARGET_DIR/PG_VERSION" 2>/dev/null)" != "$TARGET_MAJOR" ]; then
        die "pgautoupgrade failed (exit $status) without leaving a partial upgrade behind. Fix the cause shown above and deploy again."
    fi
    rm -f "$BACKUP_MARKER"
    log "upgraded to PostgreSQL $TARGET_MAJOR"
}

cmd_check() {
    inspect
    case "$STATE" in
        fresh | current | relocate)
            echo "$STATE"
            ;;
        pending)
            echo "pending $CLUSTER_MAJOR → $TARGET_MAJOR"
            return 10
            ;;
        recover)
            echo "recover"
            return 20
            ;;
    esac
}

cmd_mark_backup() {
    local ref=${1:?backup reference required}
    inspect
    [ "$STATE" = pending ] || die "no upgrade pending (state: $STATE)"
    # a running server keeps changing pg_control
    require_stopped
    mkdir -p "$STATE_DIR"
    printf 'from=%s\ncontrol=%s\nref=%s\n' "$CLUSTER_MAJOR" "$(control_checksum)" "$ref" > "$BACKUP_MARKER.tmp"
    mv "$BACKUP_MARKER.tmp" "$BACKUP_MARKER"
    sync "$BACKUP_MARKER"
}

cmd_has_backup() {
    inspect
    [ "$STATE" = pending ] && backup_marker_matches
}

cmd_backup_ref() {
    if [ -f "$BACKUP_MARKER" ]; then
        sed -n 's/^ref=//p' "$BACKUP_MARKER"
    fi
}

cmd_set_aside() {
    local entries name size_kb free_kb reserve_kb
    finish_relocation
    if [ -f "$RECOVERY_MARKER" ]; then
        name=$(recovery_field aside)
        if [ "$(recovery_field phase)" = restoring ]; then
            # what the mount holds now is the database started for the restore, which is retried into it
            log "the old database files are already set aside in db/data/$name"
            echo "$name"
            return 0
        fi
        log "continuing to set the old database files aside in db/data/$name"
    else
        if [ "${DB_UPGRADE_REQUIRE_BACKUP:-}" = 1 ] && [ ! -f "$BACKUP_MARKER" ]; then
            die "no pre-upgrade backup is recorded to restore the database from, refusing to set its files aside"
        fi
        entries=$(all_entries)
        if [ -z "$entries" ]; then
            log "nothing to set aside"
            return 0
        fi
        # The move itself is free; the restore that follows needs about as much space as the data.
        # shellcheck disable=SC2086
        size_kb=$(du -skc $entries | tail -n 1 | cut -f 1)
        free_kb=$(df -Pk "$ROOT" | awk 'NR == 2 { print $4 }')
        reserve_kb=$(( ${DB_UPGRADE_RESERVE_MB:-1024} * 1024 ))
        if [ "$free_kb" -lt $(( size_kb + reserve_kb )) ]; then
            die "not enough disk space to restore: need $(( (size_kb + reserve_kb) / 1024 )) MB free, have $(( free_kb / 1024 )) MB"
        fi
        name=".failed-$(date -u +%Y%m%dT%H%M%SZ)"
        mkdir "$ROOT/$name"
        write_recovery_marker "$name" moving
    fi
    all_entries | while read -r entry; do
        mv "$entry" "$ROOT/$name/"
    done
    sync "$ROOT/$name"
    write_recovery_marker "$name" restoring
    log "set the old database files aside in db/data/$name"
    echo "$name"
}

cmd_cleanup() {
    local before=${1:?timestamp required} dir stamp
    if [ -f "$RECOVERY_MARKER" ]; then
        log "a recovery did not finish, keeping the set-aside database files"
        return 0
    fi
    for dir in "$ROOT"/.failed-*; do
        [ -d "$dir" ] || continue
        stamp=${dir##*/.failed-}
        if [[ "$stamp" < "$before" ]]; then
            log "deleting db/data/.failed-$stamp"
            rm -rf "$dir"
        fi
    done
}

cmd_requires_backup() {
    if [ "${DB_UPGRADE_REQUIRE_BACKUP:-}" = 1 ]; then
        echo yes
    else
        echo no
    fi
}

command=${1:-run}
shift || true
case "$command" in
    run) cmd_run ;;
    check) cmd_check ;;
    mark-backup) cmd_mark_backup "$@" ;;
    has-backup) cmd_has_backup ;;
    backup-ref) cmd_backup_ref ;;
    requires-backup) cmd_requires_backup ;;
    set-aside) cmd_set_aside ;;
    finish-recovery) rm -f "$BACKUP_MARKER" "$RECOVERY_MARKER" ;;
    cleanup) cmd_cleanup "$@" ;;
    *) die "unknown command: $command" ;;
esac
