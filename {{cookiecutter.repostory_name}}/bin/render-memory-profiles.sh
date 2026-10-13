#!/bin/sh
# Render a temporal flame graph for memray captures in ./profiles, inside the app
# image so the memray version matches the one that wrote them. Each report is
# written next to its capture as <capture>.html, so forked children
# (<capture>.bin.<pid>) keep their pid and never overwrite each other.
# Run it after switching MEMORY_PROFILING back to 0, so the captures are complete.
# Usage, from the project root:
#   bin/render-memory-profiles.sh                   # every capture without a report yet
#   bin/render-memory-profiles.sh gunicorn-*.bin*   # only these (names as in ./profiles)
set -eu
cd "$(dirname "$0")/.."

if [ "$#" -eq 0 ]; then
    set -- profiles/*.bin profiles/*.bin.[0-9]*
fi
names=""
for capture in "$@"; do
    names="$names $(basename "$capture")"
done

# shellcheck disable=SC2016,SC2086
docker compose run --rm --no-deps app sh -c '
    for name in "$@"; do
        [ -e "/var/profiles/$name" ] || continue
        [ -e "/var/profiles/$name.html" ] && continue
        memray flamegraph --temporal -o "/var/profiles/$name.html" "/var/profiles/$name"
    done
' render-memory-profiles $names
