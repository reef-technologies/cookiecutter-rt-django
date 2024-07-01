# RT cookiecutter template selling points

## Main features

- Cookiecutter template allowing long term support using [Cruft](https://github.com/cruft/cruft) update mechanism
- [Docker](https://www.docker.com) and [docker compose](https://docs.docker.com/compose/) for easy & simple (c) development and deployment
- Latest [python](https://www.python.org) from 3.11 line
- Latest [Django](https://www.djangoproject.com) LTS release
- [Gunicorn](https://gunicorn.org) for running WSGI instances on prod
- [Uvicorn](https://www.uvicorn.org) for ASGI instances on prod
- [Nginx](https://www.nginx.com) as high-performance reverse proxy with automatic SSL certificate renewal
- [Postgres](https://www.postgresql.org) with [psycopg3](https://www.psycopg.org/psycopg3) for database
- Task management via [celery](https://docs.celeryproject.org) with scheduled tasks support (using celery-beat)
- Multiple workers & queues supported (if you need to divide / prioritize tasks and apply different levels of concurrency)

## Self-hosted configuration

- Persistent [redis](https://redis.io) for task management backend
- Celery task monitoring via [flower](https://flower.readthedocs.io/en/latest/)

## Cloud configuration options

- AWS support:
  terraform to deploy RDS, SQS, ELB etc
- Vultr: terraform for deploying application on cheap VPS servers
- Support for transaction-based database connection pooling

## Configuration

- [.env files](https://12factor.net/config) for configuration; preconfigured `.env` for both local and prod environments
- [django-debug-toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/) (enabled for local environment) for debugging app performance
- [ipython](https://ipython.org) included for nice interactive django shell
- [django-extensions](https://django-extensions.readthedocs.io/en/latest/) for drawing graph of models and more

## Continuous integration

- Github Actions for CI/CD
- [nox](https://nox.thea.codes) for workflow automation
- [ruff](https://github.com/astral-sh/ruff) for linting & auto fixing python code
- [shellcheck](https://www.shellcheck.net) for linting & auto fixing shell scripts
- [pytest](https://docs.pytest.org) with xdist for efficient parallel testing

## Deployment

- [2-stage docker image build](https://docs.docker.com/develop/develop-images/multistage-build/) for clean app image (both debian-based and alpine-based base images are supported)
- Easy deployment based on `git push production master`
- Redeployment doesn't stop `db`, `redis` and `nginx` containers -> non-interrupted deployments
- Migrations are done during deployment, before application startup -> application won't be run on unmigrated database

## Security & performance

- [CORS headers](https://en.wikipedia.org/wiki/Cross-origin_resource_sharing) preconfigured
- [CSP](https://en.wikipedia.org/wiki/Content_Security_Policy) integrated
- [BREACH attack](https://en.wikipedia.org/wiki/BREACH) mitigation
- Brotli compression support
- 0-RTT TLS 1.3 Early Data support
- [http/2](https://en.wikipedia.org/wiki/HTTP/2) support
- [TLS 1.2&1.3](https://en.wikipedia.org/wiki/Transport_Layer_Security) via [letsencrypt](https://letsencrypt.org) with auto-renewal
- Forward secrecy ciphers
- Overall ssllabs security class:
  A+ 100/100/90/90 (to keep compatibility with some older clients)
- Optional fingerprinting of users on backend and frontend sides

## Reliability

- Cost-efficient & secure automatic database backups
  - [B2](https://www.backblaze.com/b2/cloud-storage.html) cloud storage using a `writeFiles`-only key with and option to store them locally or send them over email
  - zstd compression for efficient storage & excellent speed for both backup and restore
- Scripted and repeatable procedure for restoring the system from a backup
- [Sentry](https://sentry.io) error tracking preconfigured
- Grafana for metrics and log aggregation (Grafana Loki)
  - Prometheus for data collection
  - Grafana Loki for log aggregation with Promtail for log shipping
  - Generic host dashboard section optimized for both VM and physical machines
  - nginx-level dashboard section for http/ws statistics
  - Active monitoring dashboard (http ping)
  - Alert history dashboard
- Alertmanager for detecting issues and alerting
