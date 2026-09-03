# db/init

Scripts here run **once**, when the postgres data directory is first initialised
(they are mounted at `/docker-entrypoint-initdb.d/`). They never run again — not on
restarts, and not on an already-deployed database.

## The exporter role is opt-in

`01-monitoring.sh` always creates the `pg_stat_statements` extension. The dedicated
exporter role is only created when both `POSTGRES_EXPORTER_USER` and
`POSTGRES_EXPORTER_PASSWORD` are set; left blank, the postgres-exporter container
connects as `POSTGRES_USER` and everything still works. Set both in `.env` to
separate monitoring load from application load in the stats.

## Applying to an existing database

Run the same statements by hand, substituting the values from `.env`:

```sh
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'EOSQL'
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE ROLE <POSTGRES_EXPORTER_USER> WITH LOGIN PASSWORD '<POSTGRES_EXPORTER_PASSWORD>';
GRANT pg_monitor TO <POSTGRES_EXPORTER_USER>;
EOSQL
```

`CREATE EXTENSION` requires the `db` container to be running with
`pg_stat_statements` in `shared_preload_libraries` (set in the compose file) — if it
predates that config, recreate it first: `docker compose up -d --force-recreate db`.

## One role per consumer

`pg_stat_statements` and `pg_stat_activity` attribute queries to the database role
that ran them, and the dashboard groups by role. To tell the application's load
apart from another consumer (e.g. a Grafana instance querying this database
directly), give that consumer its own role — read-only, with a
`statement_timeout` — via an additional `02-*.sh` script here or by hand.
