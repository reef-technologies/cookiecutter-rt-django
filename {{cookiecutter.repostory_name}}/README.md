# {{ cookiecutter.repostory_name }}

{{ cookiecutter.project_short_description }}

- - -

# Base requirements

- docker with [compose plugin](https://docs.docker.com/compose/install/linux/)
- python 3.11
- [uv](https://docs.astral.sh/uv/)
- [nox](https://nox.thea.codes)

# Setup development environment

```sh
./setup-dev.sh
docker compose up -d
cd app/src
uv run manage.py wait_for_database --timeout 10
uv run manage.py migrate
uv run manage.py runserver
```

# Setup production environment (git deployment)

<details>

This sets up "deployment by pushing to git storage on remote", so that:

- `git push origin ...` just pushes code to Github / other storage without any consequences;
- `git push production master` pushes code to a remote server running the app and triggers a git hook to redeploy the application.

```
Local .git ------------> Origin .git
                \
                 ------> Production .git (redeploy on push)
```

- - -

Use `ssh-keygen` to generate a key pair for the server, then add read-only access to repository in "deployment keys" section (`ssh -A` is easy to use, but not safe).

```sh
# remote server
mkdir -p ~/repos
cd ~/repos
git init --bare --initial-branch=master {{ cookiecutter.repostory_name }}.git

mkdir -p ~/domains/{{ cookiecutter.repostory_name }}
```

```sh
# locally
git remote add production root@<server>:~/repos/{{ cookiecutter.repostory_name }}.git
git push production master
```

```sh
# remote server
cd ~/repos/{{ cookiecutter.repostory_name }}.git

cat <<'EOT' > hooks/post-receive
#!/bin/bash
unset GIT_INDEX_FILE
export ROOT=/root
export REPO={{ cookiecutter.repostory_name }}
while read oldrev newrev ref
do
    if [[ $ref =~ .*/master$ ]]; then
        export GIT_DIR="$ROOT/repos/$REPO.git/"
        export GIT_WORK_TREE="$ROOT/domains/$REPO/"
        git checkout -f master
        cd $GIT_WORK_TREE
        ./deploy.sh
    else
        echo "Doing nothing: only the master branch may be deployed on this server."
    fi
done
EOT

chmod +x hooks/post-receive
./hooks/post-receive
cd ~/domains/{{ cookiecutter.repostory_name }}
sudo bin/prepare-os.sh
./setup-prod.sh

# adjust the `.env` file

mkdir letsencrypt
./letsencrypt_setup.sh
./deploy.sh
```

### Deploy another branch

Only `master` branch is used to redeploy an application.
If one wants to deploy other branch, force may be used to push desired branch to remote's `master`:

```sh
git push --force production local-branch-to-deploy:master
```

</details>

{% if cookiecutter.use_allauth == 'y' %}
# External auth (OAuth, OpenID connect etc.)
To configure an external authentication mechanism, usually you must acquire a "client ID" and a "client secret".
This usually requires registering your application on the provider's website. Look at allauth's documentation for the
specific provider to see how to do that:

[https://docs.allauth.org/en/latest/socialaccount/providers/index.html](https://docs.allauth.org/en/latest/socialaccount/providers/index.html)

After acquiring the id and secret, simply fill in the env vars for the provider.
{% if cookiecutter.allauth_trust_external_emails == "y" %}

> ⚠️ Caution: the SSO provider is trusted to have verified the ownership of user's email address.
> This will allow a user to log in to any account that matches the email address returned by the
> SSO provider, whether the account is connected with the provider or not.

{% endif %}

{% if 'openid_connect' in cookiecutter.allauth_providers %}
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

{% endif %}

{% if cookiecutter.use_celery == 'y' %}
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
{% if cookiecutter.monitoring == 'y' %}
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

## Vultr

<details>
Initiate the infrastructure with Terraform and cloud-init:

- see Terraform template in `<project>/devops/vultr_tf/core/`
- see scripts for interacting with Vultr API in `<project>/devops/vultr_scripts/`
  - note these scripts need `vultr-cli` installed

For more details see [README_vultr.md](README_vultr.md).
</details>

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

Set env vars:
- `BACKUP_B2_BUCKET`
- `BACKUP_B2_KEY_ID`
- `BACKUP_B2_KEY_SECRET`

Backups will be stored in the bucket, no rotation is performed.

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

# cookiecutter-rt-django

Skeleton of this project was generated using [cookiecutter-rt-django](https://github.com/reef-technologies/cookiecutter-rt-django).
Use `cruft update` to update the project to the latest version of the template with all current bugfixes and [features](https://github.com/reef-technologies/cookiecutter-rt-django/blob/master/features.md).
