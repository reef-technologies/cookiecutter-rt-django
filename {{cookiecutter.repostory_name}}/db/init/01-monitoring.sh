#!/bin/bash
# Executed by the postgres image on first initialisation of the data directory only.
# For an existing database, run the same statements by hand — see db/init/README.md.
set -euo pipefail
{% if cookiecutter.monitoring %}
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

# The dedicated exporter role is opt-in: unless BOTH exporter variables are set, the
# exporter falls back to the application user (see the compose file), so skip it.
if [ -z "${POSTGRES_EXPORTER_USER:-}" ] || [ -z "${POSTGRES_EXPORTER_PASSWORD:-}" ]; then
    echo "01-monitoring.sh: POSTGRES_EXPORTER_USER and POSTGRES_EXPORTER_PASSWORD not both set; skipping monitoring role creation (exporter will use POSTGRES_USER)"
    exit 0
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- read-only monitoring role for postgres-exporter; pg_monitor grants access to
    -- pg_stat_* views, including full query text in pg_stat_statements
    CREATE ROLE "$POSTGRES_EXPORTER_USER" WITH LOGIN PASSWORD '$POSTGRES_EXPORTER_PASSWORD';
    GRANT pg_monitor TO "$POSTGRES_EXPORTER_USER";
    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO "$POSTGRES_EXPORTER_USER";
EOSQL
{% else %}
echo "monitoring disabled: no database initialisation to do"
{% endif %}
