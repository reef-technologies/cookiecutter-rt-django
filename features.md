# RT cookiecutter template selling points

## Main configuration

- [Cookiecutter](https://github.com/cookiecutter/cookiecutter) template
- Template updates using [Cruft](https://github.com/cruft/cruft)
- [Docker](https://www.docker.com) and [docker-compose](https://docs.docker.com/compose/) for easy & simple (c) development and deployment
- Latest [python](https://www.python.org) from 3.9 line (due to [nogil fork compatibility](https://www.backblaze.com/blog/python-gil-vs-nogil-boost-i-o-performance-10x-with-one-line-change/))
- Latest [Django](https://www.djangoproject.com) LTS release
- [Gunicorn](https://gunicorn.org) for running WSGI instances on prod
- [Uvicorn](https://www.uvicorn.org) for ASGI instances on prod
- [Postgres](https://www.postgresql.org) for database
- Task management via [celery](https://docs.celeryproject.org)
- Multiple workers & queues supported (if you need to divide / prioritize tasks and apply different levels of concurrency)

## Self-hosted configuration

- Persistent [redis](https://redis.io) for task management backend
- Celery task monitoring via [flower](https://flower.readthedocs.io/en/latest/)

## Cloud configuration

- AWS terraform to deploy RDS, SQS, ELB etc

## Configuration

- [.env files](https://12factor.net/config) for configuration; preconfigured `.env` for both local and prod environments
- [django-debug-toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/) (enabled for local environment) for debugging app performance
- [ipython](https://ipython.org) included for nice interactive django shell
- [django-extensions](https://django-extensions.readthedocs.io/en/latest/) for drawing graph of models and more

## Deployment

- [2-stage docker image build](https://docs.docker.com/develop/develop-images/multistage-build/) for clean app image
- Easy deployment based on `git push production master`
- Redeployment doesn't stop `db`, `redis` and `nginx` containers -> non-interrupted deployments
- Migrations are done during deployment, before application startup -> application won't be run on unmigrated database

## Security

- [CORS headers](https://en.wikipedia.org/wiki/Cross-origin_resource_sharing) preconfigured
- [CSP](https://en.wikipedia.org/wiki/Content_Security_Policy) integrated
- Compression is off by default to avoid [BREACH attack](https://en.wikipedia.org/wiki/BREACH)
- Brotli compression support
- [http/2](https://en.wikipedia.org/wiki/HTTP/2) support
- [TLS 1.2&1.3](https://en.wikipedia.org/wiki/Transport_Layer_Security) via [letsencrypt](https://letsencrypt.org) with auto-renewal
- Forward secrecy ciphers
- Overall ssllabs security class:
  A+ 100/100/90/90 (to keep compatibility with some older clients)
- Optional fingerprinting of users on backend and frontend sides

## Reliability

- Backups to:
  - Host system
  - [B2](https://www.backblaze.com/b2/cloud-storage.html) using a `writeFiles`-only key
  - Email
- Script and a written procedure for restoring the system from a backup
- [Sentry](https://sentry.io) error tracking preconfigured
- Prometheus for data collection
- Grafana for metrics
  - Generic host dashboard section optimized for both VM and physical machines
  - nginx-level dashboard section for http/ws statistics
  - Active monitoring dashboard (http ping)
  - Alert history dashboard
- Alertmanager for detecting issues and alerting
