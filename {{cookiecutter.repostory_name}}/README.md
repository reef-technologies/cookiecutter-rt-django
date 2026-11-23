# {{ cookiecutter.repostory_name }}

{{ cookiecutter.project_short_description }}

What users can do is described in [USER_STORIES.md](USER_STORIES.md).

- - -

# Base requirements

- [docker](https://docs.docker.com)
- [uv](https://docs.astral.sh/uv/)

# Setup development environment

```sh
./setup-dev.sh
docker compose up -d
cd app/src
uv run manage.py wait_for_database --timeout 10
uv run manage.py migrate
uv run manage.py runserver
```
{% if cookiecutter.deployment_type == 'direct' %}

# Setup production environment (git deployment)

Direct deployment uses a Git remote named `production` pointing to a bare repository on the application server.
Each push to that server's `master` branch runs `./deploy.sh` through an `update` hook.
The server advances `master` only when deployment succeeds; a deployment failure rejects the branch update and makes `git push` fail.
`production` is a remote name; you do not need to create a branch with that name.

- `origin` points to GitHub or your other source repository. Pushing there does not trigger this direct deployment hook.
- `production` points to the application server. Pushing to its `master` branch deploys the application.
- Your local branch can be named `main`, `master`, or anything else. `HEAD:master` pushes your currently checked-out commit to the server's `master` branch.

## Prerequisites

- An Ubuntu server with Git and `ufw` installed. `bin/prepare-os.sh` installs Docker, the Compose plugin and other host dependencies.
- SSH access from your computer as `root`. Replace `<server>` below with the server's hostname or IP address. Install your computer's public SSH key in `/root/.ssh/authorized_keys` on the server, and verify that `ssh root@<server>` works.
- A committed application version in your local repository. Git pushes send committed files only.
- A hostname and TLS certificates; see [TLS certificates](#tls-certificates) for public and internal deployments. Allow inbound TCP ports 80 and 443 through the host and provider firewalls for a public deployment.

The paths and hook below assume the SSH user is `root` and its home directory is `/root`.
Code is pushed from your computer to the server, so the server does not need a GitHub deploy key or SSH agent forwarding for this workflow.

## 1. Create the server repository

On the server, logged in as `root`:

```sh
mkdir -p ~/repos
cd ~/repos
git init --bare --initial-branch=master {{ cookiecutter.repostory_name }}.git
mkdir -p ~/domains/{{ cookiecutter.repostory_name }}
```

## 2. Add the remote and upload the initial version

On your computer, from the application repository:

```sh
git remote add production root@<server>:~/repos/{{ cookiecutter.repostory_name }}.git
git remote -v
git push production HEAD:master
```

Remotes are local to each clone: every owner or maintainer who deploys must add this remote on their own computer.
If `production` already exists, inspect its URL with `git remote get-url production`; use `git remote set-url production root@<server>:~/repos/{{ cookiecutter.repostory_name }}.git` if it needs correcting.

This initial push only uploads the code. Install the deployment hook after completing the first deployment below.

## 3. Check out and configure the application

On the server, logged in as `root`:

```sh
export GIT_DIR=/root/repos/{{ cookiecutter.repostory_name }}.git
export GIT_WORK_TREE=/root/domains/{{ cookiecutter.repostory_name }}
git checkout -f master
cd "$GIT_WORK_TREE"
bin/prepare-os.sh
./setup-prod.sh
```

Keep this server shell open for the next step. The exported variables let Git find the bare repository from the application directory.
Edit `envs/prod/.env` (`.env` is a symlink to it), filling in secrets, database and backup settings and `NGINX_HOST`.
Configure any credentials required by enabled monitoring and observability services as well.
These environment files stay on the server and are not committed to Git.

## 4. Run the first deployment

In the same server shell, from the application directory:

```sh
mkdir -p letsencrypt
./letsencrypt_setup.sh  # or ./selfsign_setup.sh; see "TLS certificates" below
./deploy.sh
docker compose ps
```

Check that the application is reachable over HTTPS before enabling deployment on push.
`deploy.sh` builds the application, pulls service images, backs up the database, stops the app and Celery services for migrations, and starts the services again. Deployments include a period of downtime.

## 5. Enable deployment on push

After the first deployment succeeds, install the hook on the server:

```sh
cd ~/repos/{{ cookiecutter.repostory_name }}.git
install -m 0755 /root/domains/{{ cookiecutter.repostory_name }}/bin/deploy-update-hook.sh hooks/update
if [ -f hooks/post-receive ]; then
    chmod -x hooks/post-receive
fi
```

Git invokes `hooks/update` with the branch name and old/new commit IDs before updating the branch. There is no separate manual invocation step.
The hook checks out the incoming commit with a detached HEAD, then deploys it. This ensures the build uses the incoming version while `master` still points to the previously accepted version.
The installation disables any `post-receive` hook to prevent a second deployment after the push.
The installed hook is a copy outside the checked-out application. After changing `bin/deploy-update-hook.sh`, repeat this installation step on the server.

## Deploy updates

On your computer, check out the committed version you want to deploy, then run:

```sh
git push production HEAD:master
```

Watch the push output for the deployment result. `git push production main:master` and `git push production master:master` explicitly select a local branch instead.
Pushing to another branch on the `production` remote only stores that branch; the hook deploys updates to `master` only.
The hook rejects attempts to delete `master`.
Deploy one version at a time and wait for it to finish before starting another push.

### Deploy a different branch or an older commit

For a different local branch whose history includes the deployed version:

```sh
git push production local-branch-to-deploy:master
```

If Git rejects it as a non-fast-forward update, first review the currently deployed version with `git fetch production` and `git log -1 production/master`.
To deliberately replace that version after review:

```sh
git push --force-with-lease production local-branch-to-deploy:master
```

This replaces the server's branch history and deploys the selected version. Database backups and migrations still run; deploying older code does not reverse database migrations.

### Retry a failed deployment

If deployment fails, `git push` reports `hook declined` and the server's `master` remains at its previous commit.
Inspect the push output and the server's `docker compose ps` / `docker compose logs` output, then fix the cause. If a maintenance or optimization task blocks deployment, wait for it to finish or stop it according to that project's runbook.
Retry the same command from your computer; the branch update was rejected, so this runs deployment again:

```sh
git push production HEAD:master
```

Rejection does not roll back the checked-out files, database migrations or container changes already performed. Inspect the application's state after a partial deployment failure.
Git acceptance and deployment are not a single transaction: a connection failure or a reference update error after deployment may still require checking the server before retrying.

To rerun deployment of the currently checked-out code independently of a push, log in to the server as `root` and run:

```sh
export GIT_DIR=/root/repos/{{ cookiecutter.repostory_name }}.git
export GIT_WORK_TREE=/root/domains/{{ cookiecutter.repostory_name }}
cd "$GIT_WORK_TREE"
./deploy.sh
docker compose ps
```

# TLS certificates

`nginx/templates/default.conf.template` reads four files, and the `nginx` service bind-mounts `./letsencrypt/etc` into `/etc/letsencrypt` to supply them:

| Path inside the container | Path on the host |
|---|---|
| `/etc/letsencrypt/dhparams/dhparam.pem` | `letsencrypt/etc/dhparams/dhparam.pem` |
| `/etc/letsencrypt/live/$NGINX_HOST/fullchain.pem` | `letsencrypt/etc/live/$NGINX_HOST/fullchain.pem` |
| `/etc/letsencrypt/live/$NGINX_HOST/privkey.pem` | `letsencrypt/etc/live/$NGINX_HOST/privkey.pem` |
| `/etc/letsencrypt/live/$NGINX_HOST/chain.pem` | `letsencrypt/etc/live/$NGINX_HOST/chain.pem` |

**Two scripts produce exactly those four files, so the choice between them changes nothing else in the deployment.** `letsencrypt/` is gitignored, and `NGINX_HOST` must be set in `.env` before either runs: it names the `live/` directory the certificate is written to, and nginx substitutes it into `server_name`.
{% if cookiecutter.monitoring %}

The monitoring vhost on port `10443` is independent of both. It uses the mutually authenticated pair under `nginx/monitoring_certs/` described in that directory's README, and neither script touches it.
{% endif %}

## Let's Encrypt (default)

`./letsencrypt_setup.sh` issues a publicly trusted certificate through certbot's standalone HTTP-01 challenge. It needs `NGINX_HOST` to resolve publicly to this host with port 80 reachable from the internet, and it binds port 80 itself — so on a deployment that is already serving, stop `nginx` for the duration of the run.

## Self-signed

`./selfsign_setup.sh` issues a self-signed certificate instead, for deployments where ACME is not an option: no public DNS name, port 80 unreachable, or a host that is internal by design. It needs nothing but Docker and a `NGINX_HOST` value, and it takes the hostname from `.env` the same way, emitting an `IP:` rather than a `DNS:` subject alternative name when that value is an address literal.

```sh
mkdir -p letsencrypt
./selfsign_setup.sh
docker compose up -d --force-recreate nginx
```

Like certbot's `certonly`, it keeps a certificate that is still valid rather than reissuing one, so rerunning the deployment steps will not invalidate the certificate clients were told to trust. Reissue deliberately with `./selfsign_setup.sh --force`. The Diffie-Hellman parameter is generated once and survives a reissue.

Three consequences, none of which apply to the Let's Encrypt path:

- **Every client has to be told to trust it.** Nothing chains to a public root, so each caller needs the certificate in its trust store, `curl --cacert letsencrypt/etc/live/$NGINX_HOST/fullchain.pem`, or verification disabled. The script prints the certificate's SHA-256 fingerprint so that what a client trusts can be checked against what the server actually serves.
- **HSTS makes the switch one-way in a browser.** The main vhost sends `Strict-Transport-Security: max-age=31536000`. A browser that has already reached this hostname over a publicly trusted certificate will refuse to offer a click-through warning for a self-signed one, for up to a year and regardless of what the server now sends. Only a hostname no browser has visited over HTTPS is unaffected.
- **Nothing renews it.** The certificate is valid for ten years and no certbot timer will replace it.

Verify what is being served, from a host that can reach the deployment:

```sh
openssl s_client -connect "$NGINX_HOST:443" -servername "$NGINX_HOST" </dev/null 2>/dev/null \
    | openssl x509 -noout -subject -issuer -dates -ext subjectAltName

# succeeds only if the served certificate is the one in this file
curl --cacert "letsencrypt/etc/live/$NGINX_HOST/fullchain.pem" -sSI "https://$NGINX_HOST/"
```
{% endif %}

{% if cookiecutter.use_allauth %}
# External auth (OAuth, OpenID connect etc.)
To configure an external authentication mechanism, usually you must acquire a "client ID" and a "client secret".
This usually requires registering your application on the provider's website. Look at allauth's documentation for the
specific provider to see how to do that:

[https://docs.allauth.org/en/latest/socialaccount/providers/index.html](https://docs.allauth.org/en/latest/socialaccount/providers/index.html)

After acquiring the id and secret, simply fill in the env vars for the provider.
{% if cookiecutter.allauth_trust_external_emails %}

> ⚠️ Caution: the SSO provider is trusted to have verified the ownership of user's email address.
> This will allow a user to log in to any account that matches the email address returned by the
> SSO provider, whether the account is connected with the provider or not.

{% endif %}

{% if 'openid_connect' in cookiecutter.allauth_providers.split(",")|map("trim") %}
## Setting up a generic OpenID Connect service
<details>
If an SSO provider supports the OIDC protocol, it can be set up as a generic OIDC provider here:

1. Come up with a new `provider_id`
   - it's just an arbitrary alphanumerical string to identify the provider in the app
   - it must be unique in the scope of the app
   - it should not collide with the name of an installed provider type - so don't use `gitlab`, `google` or similar
   - something like `rt_keycloak` would be OK
2. Register the app with the provider to acquire a `client_id`, a `secret` and the URL for the openid config (e.g. https://gitlab.com/.well-known/openid-configuration)
   - When asked for callback / redirect url, use `https://{domain}/accounts/oidc/{provider_id}/login/callback/`
   - For development, usually http://127.0.0.1:8000 can be used as the base URL here
3. Fill in the `OPENID_CONNECT_*` env vars
   - `OPENID_CONNECT_NICE_NAME` is just a human-readable name, it will be later shown on login form (Log in with {name}...)
   - the `OPENID_CONNECT_SERVER_URL` value is just the URL **before** the .well-known part, so for https://gitlab.com/.well-known/openid-configuration this is just https://gitlab.com
</details>

{% endif %}
## Allauth users in django
1. Allauth does not disable django's authentication. It lives next to it as an alternative. You can still access django admin login.
2. Allauth "social users" are just an extension to regular django users. When someone logs in via allauth, a django user model will also be created for them.
3. A "profile" page is available at `/accounts/`

{% if cookiecutter.allauth_staff_email_domain %}
## Granting staff access to allauth users
If "social user"'s email belongs to `SOCIALACCOUNT_STAFF_EMAIL_DOMAIN`, they will be granted staff access on account creation.
{% endif %}

{% endif %}

{% if cookiecutter.use_celery %}
# Background tasks with Celery

## Dead letter queue

<details>
There is a special queue named `dead_letter` that is used to store tasks
that failed for some reason.

A task should be annotated with `on_failure=send_to_dead_letter_queue`.
Once the reason of tasks failure is fixed, the task can be re-processed
by moving tasks from dead letter queue to the main one ("celery"):

    manage.py move_tasks "dead_letter" "celery"

If tasks fails again, it will be put back to dead letter queue.

To flush add tasks in specific queue, use

    manage.py flush_tasks "dead_letter"
</details>

{% endif %}

{% if cookiecutter.observability %}
# Observability (logs, metrics, traces)

Logs go to Grafana Loki, metrics to Prometheus/Mimir and OpenTelemetry traces to Grafana Tempo. Grafana Alloy runs alongside the app in `docker-compose` and ships logs to Loki plus traces to Tempo; metrics are collected by Prometheus and forwarded to Mimir. `trace_id`/`span_id` are injected into structured logs and nginx access logs so a request can be followed across all three signals.

## Loki & Tempo credentials

Generate new access credentials to Loki server.
- `<SERVER_GROUP>` should be taken from Grafana's `client_server_group` options (so that we can automatically show logs in Grafana); Example: `rt_rat`
- `<ENVIRONMENT>` is usually `prod`
```sh
uvx cadm exec prometheus -- "cd /home/ubuntu/apps/prometheus-grafana-monitoring/scripts && ./add_loki_target.sh <SERVER_GROUP> <ENVIRONMENT>"
```
Then put the output in `.env` file's `LOKI_USER` and `LOKI_PASSWORD` fields.

**Tempo uses the same credentials.** The `.htpasswd` file on the monitoring server is [shared between Loki, Mimir and Tempo](https://github.com/reef-technologies/prometheus-grafana-monitoring?tab=readme-ov-file#adding-monitored-targets-multi-tenancy-way), so set `TEMPO_USER` and `TEMPO_PASSWORD` in `.env` to the same values as `LOKI_USER` / `LOKI_PASSWORD`.

More on configuration [here](https://github.com/reef-technologies/prometheus-grafana-monitoring?tab=readme-ov-file#adding-log-aggregation-targets).

## OpenTelemetry environment variables

The following variables describe the deployed service in traces, metrics and logs. Most are set in `.env`; `GIT_SHA` is baked into the application Docker image at build time.

- `OTEL_SERVICE_NAMESPACE` — namespace of the project, defaults to the repository name. Shared by every service of one project (app, celery, celery-beat, nginx).
- `OTEL_DEPLOYMENT_ENVIRONMENT` — `development` / `staging` / `production`. Used for filtering in Grafana.
- `OTEL_SERVICE_INSTANCE_ID` — optional stable id for a worker. If left empty, every worker generates a fresh random UUID at startup, which is fine for autoscaled instances.
- `GIT_SHA` — version of the running code, exposed as `service.version`. {% if cookiecutter.deployment_type == 'aws' %}`devops/scripts/build-backend.sh`{% else %}`deploy.sh`{% endif %} computes it from `git rev-parse --short HEAD`, passes it as the Docker build arg `GIT_SHA`, and the application image stores it permanently as `GIT_SHA` and `OTEL_SERVICE_VERSION`. For manual builds, export `GIT_SHA` before `docker compose build`; otherwise it defaults to `unknown`.

`OTEL_EXPORTER_OTLP_ENDPOINT` points at the local Alloy collector (`http://alloy:4318` in docker-compose). Do not point the app directly at `tempo.reef.pl` — Alloy handles batching, tail-sampling and auth.

## Local development

Tracing is **disabled by default in dev** via `OTEL_SDK_DISABLED=true` in `envs/dev/.env.template`. The OpenTelemetry bootstrap returns before loading auto-instrumentations or starting the SDK, so there is zero traffic to any collector. To debug traces locally either:

- set `OTEL_SDK_DISABLED=false` and run a local Alloy + Tempo (or any OTLP-compatible collector listening on `localhost:4318`), or
- temporarily point `OTEL_EXPORTER_OTLP_ENDPOINT` at a shared dev collector.

Local tracing is initialized by the gunicorn worker hooks, so it works only when the app is run through gunicorn. The default `uv run manage.py runserver` development command does not start the OpenTelemetry SDK/exporter.

## Trace ↔ log correlation in Grafana

Every structlog record and every nginx access log line carries the active `trace_id` and `span_id`. In Grafana the Loki data source is configured with a derived field on `trace_id` that links to the Tempo data source, so you can jump from a log line to the full trace in one click (and from a Tempo span back to the related logs).
{% endif %}

{% if cookiecutter.monitoring %}
# Monitoring

Running the app requires proper certificates to be put into `nginx/monitoring_certs`,
see [nginx/monitoring_certs/README.md](nginx/monitoring_certs/README.md) for more details.

## Monitoring execution time of code blocks

Somewhere, probably in `metrics.py`:

```python
some_calculation_time = prometheus_client.Histogram(
    'some_calculation_time',
    'How Long it took to calculate something',
    namespace='django',
    unit='seconds',
    labelnames=['task_type_for_example'],
    buckets=[0.5, 1, *range(2, 30, 2), *range(30, 75, 5), *range(75, 135, 15)]
)
```

Somewhere else:

```python
with some_calculation_time.labels('blabla').time():
    do_some_work()
```

{% endif %}
{% if cookiecutter.deployment_type == 'aws' %}

# Cloud deployment

## AWS

<details>
Initiate the infrastructure with Terraform:
TODO

To push a new version of the application to AWS, just push to a branch named `deploy-$(ENVIRONMENT_NAME)`.
Typical values for `$(ENVIRONMENT_NAME)` are `prod` and `staging`.
For this to work, GitHub actions needs to be provided with credentials for an account that has the following policies enabled:

- AutoScalingFullAccess
- AmazonEC2ContainerRegistryFullAccess
- AmazonS3FullAccess

See `.github/workflows/cd.yml` to find out the secret names.

For more details see [README_AWS.md](README_AWS.md)
</details>
{% endif %}

# Backups

<details>
<summary>Click to for backup setup & recovery information</summary>

Backups are managed by `backups` container.

## Local volume

By default, backups will be created [periodically](backups/backup.cron) and stored in `backups` volume.

### Backups rotation
Set env var:
- `BACKUP_LOCAL_ROTATE_KEEP_LAST`

### Email

Local backups may be sent to email manually. Set env vars:
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`

Then run:
```sh
docker compose run --rm -e EMAIL_TARGET=youremail@domain.com backups ./backup-db.sh
```

## B2 cloud storage

> In these examples we assume that backups will be stored inside `folder`. If you want to store backups in the root folder, just use empty string instead of `folder`.

First, create a Backblaze B2 account and a bucket for backups (with [lifecycle rules](https://www.backblaze.com/docs/cloud-storage-configure-and-manage-lifecycle-rules)):

```sh
b2 bucket create --lifecycle-rule '{"daysFromHidingToDeleting": 30, "daysFromUploadingToHiding": 30, "fileNamePrefix": "folder/"}' "{{cookiecutter.repostory_name}}-backups" allPrivate
```

> If you want to add backups to already existing bucket, use `b2 bucket update` command and don't forget to list all previous lifecycle rules as well as adding the new one.

Create an application key with restricted access to a single bucket:

```sh
b2 key create --bucket "{{cookiecutter.repostory_name}}-backups" --namePrefix "folder/" "{{cookiecutter.repostory_name}}-backups-key" listBuckets,listFiles,readFiles,writeFiles
```

Fill in `.env` file:
- `BACKUP_B2_BUCKET={{cookiecutter.repostory_name}}-backups`
- `BACKUP_B2_FOLDER=folder`
- `BACKUP_B2_APPLICATION_KEY_ID=0012345abcdefgh0000000000`
- `BACKUP_B2_APPLICATION_KEY=A001bcdefgHIJKLMNOPQRSTUxx11x22`

## List all available backups

```sh
docker compose run --rm backups ./list-backups.sh
```

## Restoring system from backup after a catastrophical failure

1. Follow the instructions above to set up a new production environment
2. Restore the database using one of
```sh
docker compose run --rm backups ./restore-db.sh /var/backups/{backup-name}.dump.zstd

docker compose run --rm backups ./restore-db.sh b2://{bucket-name}/{backup-name}.dump.zstd
docker compose run --rm backups ./restore-db.sh b2id://{ID}
```
3. See if everything works
4. Make sure everything is filled up in `.env`, error reporting integration, email accounts etc

## Monitoring

`backups` container runs a simple server which [exposes essential metrics about backups](backups/bin/serve_metrics.py).

</details>

# Tests / CI

First install `nox` as tool for running tests and other checks:

```sh
# pyyaml is required for nox to read `pyproject.toml` file
uv tool install --with pyyaml nox
```

Then run desired nox session:

```sh
uvx nox -s lint
{% if cookiecutter.ci_use_typechecker %}
uvx nox -s type_check
{% endif %}
uvx nox -s test
```

# cookiecutter-rt-django

Skeleton of this project was generated using [cookiecutter-rt-django](https://github.com/reef-technologies/cookiecutter-rt-django).
Use `cruft update` to update the project to the latest version of the template with all current bugfixes and [features](https://github.com/reef-technologies/cookiecutter-rt-django/blob/master/features.md).
