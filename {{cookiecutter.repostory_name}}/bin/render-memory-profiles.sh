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
    set -- '*.bin' '*.bin.[0-9]*'
fi

# shellcheck disable=SC2016
docker compose run --rm --no-deps app sh -c '
    for pattern in "$@"; do
        pattern=${pattern##*/}
        for capture in /var/profiles/$pattern; do
            [ -f "$capture" ] || continue
            case "$capture" in
                *.html) continue ;;
            esac
            [ -e "$capture.html" ] && continue
            memray flamegraph --temporal -o "$capture.html" "$capture"
        done
    done
' render-memory-profiles "$@"
