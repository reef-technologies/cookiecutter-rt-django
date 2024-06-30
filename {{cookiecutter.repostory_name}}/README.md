# {{ cookiecutter.repostory_name }}

{{ cookiecutter.project_short_description }}

- - -

Skeleton of this project was generated with `cookiecutter-rt-django`, which sometimes gets upgrades that are easy to retrofit into already older projects.

# Base requirements

- docker with [compose plugin](https://docs.docker.com/compose/install/linux/)
- python 3.11
- [pdm](https://pdm-project.org)
- [nox](https://nox.thea.codes)

# Setup development environment

```sh
$ ./setup-dev.sh
docker compose up -d
cd app/src
pdm run manage.py wait_for_database --timeout 10
pdm run manage.py migrate
pdm run manage.py runserver
```

# Setup production environment (git deployment)

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
{% if cookiecutter.use_allauth == 'y' %}
# External auth (OAuth, OpenID connect etc.)
To configure an external authentication mechanism, usually you must acquire a "client ID" and a "client secret".
This usually requires registering your application on the provider's website. Look at allauth's documentation for the
specific provider to see how to do that:

[https://docs.allauth.org/en/latest/socialaccount/providers/index.html](https://docs.allauth.org/en/latest/socialaccount/providers/index.html)

After acquiring the id and secret, simply fill in the env vars for the provider.

{% if cookiecutter.use_allauth_openid_connect == "y" %}
## Setting up a generic OpenID Connect service
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

{% endif %} 
## Allauth users in django
1. Allauth does not disable django's authentication. It lives next to it as an alternative. You can still access django admin login.
2. Allauth "social users" are just an extension to regular django users. When someone logs in via allauth, a django user model will also be created for them.
3. A "profile" page is available at `/accounts/`

{% endif %}
{% if cookiecutter.monitoring == 'y' %}
# Monitoring

Running the app requires proper certificates to be put into `nginx/monitoring_certs`, see `README` located there.
{% endif %}
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

# AWS

Initiate the infrastructure with Terraform:
TODO

To push a new version of the application to AWS, just push to a branch named `deploy-$(ENVIRONMENT_NAME)`.
Typical values for `$(ENVIRONMENT_NAME)` are `prod` and `staging`.
For this to work, GitHub actions needs to be provided with credentials for an account that has the following policies enabled:

- AutoScalingFullAccess
- AmazonEC2ContainerRegistryFullAccess
- AmazonS3FullAccess

See `.github/workflows/cd.yml` to find out the secret names.

# Vultr

Initiate the infrastructure with Terraform and cloud-init:

- see Terraform template in `<project>/devops/vultr_tf/core/`
- see scripts for interacting with Vultr API in `<project>/devops/vultr_scripts/`
  - note these scripts need `vultr-cli` installed

- for more details see README_vultr.md

# Setting up periodic backups

Add to crontab:

```sh
# crontab -e
30 0 * * * cd ~/domains/{{ cookiecutter.repostory_name }} && ./bin/backup-db.sh > ~/backup.log 2>&1
```

Set `BACKUP_LOCAL_ROTATE_KEEP_LAST` to keep only a specific number of most recent backups in local `.backups` directory.

## Configuring offsite targets for backups

Backups are put in `.backups` directory locally, additionally then can be stored offsite in following ways:

**Backblaze**

Set in `.env` file:

- `BACKUP_B2_BUCKET_NAME`
- `BACKUP_B2_KEY_ID`
- `BACKUP_B2_KEY_SECRET`

**Email**

Set in `.env` file:

- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_TARGET`

# Restoring system from backup after a catastrophical failure

1. Follow the instructions above to set up a new production environment
2. Restore the database using bin/restore-db.sh
3. See if everything works
4. Set up backups on the new machine
5. Make sure everything is filled up in .env, error reporting integration, email accounts etc
