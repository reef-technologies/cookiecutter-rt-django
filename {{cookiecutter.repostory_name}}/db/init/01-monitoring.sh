#!/bin/bash
# Executed by the postgres image on first initialisation of the data directory only.
# For an existing database, run the same statements by hand — see db/init/README.md.
set -euo pipefail
{% if cookiecutter.monitoring %}
: "${POSTGRES_EXPORTER_PASSWORD:?POSTGRES_EXPORTER_PASSWORD must be set (see .env)}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

    -- read-only monitoring role for postgres-exporter; pg_monitor grants access to
    -- pg_stat_* views, including full query text in pg_stat_statements
    CREATE ROLE postgres_exporter WITH LOGIN PASSWORD '$POSTGRES_EXPORTER_PASSWORD';
    GRANT pg_monitor TO postgres_exporter;
    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO postgres_exporter;
EOSQL
{% else %}
echo "monitoring disabled: no database initialisation to do"
{% endif %}
