# {{ cookiecutter.repostory_name }}

{{ cookiecutter.project_short_description }}

------------------------------------------------

Skeleton of this project was generated with `cookiecutter-rt-django`, which sometimes gets upgrades that are easy to retrofit into already older projects.

# Base requirements

* docker
* docker-compose
* python 3.9

# Setup development environment

```sh
# 1st tab
$ python -m venv {{ cookiecutter.django_project_name }}
$ source {{ cookiecutter.django_project_name }}
$ ./setup-dev.sh
```

```sh
# 2nd tab
docker-compose up
```

```sh
# 1st tab
cd app/src
python manage.py wait_for_database --timeout 10
python manage.py migrate
python manage.py runserver
```

# Setup production environment (git deployment)

This sets up "deployment by pushing to git storage on remote", so that:
* `git push origin ...` just pushes code to Github / other storage without any consequences;
* `git push production master` pushes code to a remote server running the app and triggers a git hook to redeploy the application.

```
Local .git ------------> Origin .git
                \
                 ------> Production .git (redeploy on push)
```

-----

Use `ssh-keygen` to generate a key pair for the server, then add read-only access to repository in "deployment keys" section (`ssh -A` is easy to use, but not safe).


```sh
# remote server
cd ~
mkdir repos
cd repos
git init --bare {{ cookiecutter.repostory_name }}.git

cd ~
mkdir domains
cd domains
mkdir {{ cookiecutter.repostory_name }}
```

```sh
# locally
git remote add production root@<server>:~/repos/{{ cookiecutter.repostory_name }}.git
git push production master
```

```sh
# remote server
cd ~/repos/{{ cookiecutter.repostory_name }}.git

cat <<'EOT' >> hooks/post-receive
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
./setup-prod.sh

# adjust the `.env` file

mkdir letsencrypt
./letsencrypt_setup.sh
./deploy.sh
```

### Deploy another branch

Only `master` branch is used to redeploy an application. If one wants to deploy other branch, force may be used to push desired branch to remote's `master`:

```sh
git push --force production local-branch-to-deploy:master
```

{% if cookiecutter.monitoring == 'y' %}
# Monitoring

Running the app requires proper certificates to be put into `nginx/monitoring_certs`, see `README` located there.
{% endif %}

# AWS

Initiate the infrastructure with terraform:
TODO

To push a new version of the application to AWS, just push to a branch named `deploy-$(ENVIRONMENT_NAME)`. Typical
values for `$(ENVIRONMENT_NAME)` are `prod` and `staging`. For this to work, GitHub actions needs to be provided with
credentials for an account that has the following policies enabled:

- AutoScalingFullAccess
- AmazonEC2ContainerRegistryFullAccess
- AmazonS3FullAccess

See `.github/workflows/cd.yml` to find out the secret names.

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

* `BACKUP_B2_BUCKET_NAME`
* `BACKUP_B2_KEY_ID`
* `BACKUP_B2_KEY_SECRET`

**Email**

Set in `.env` file:

* `EMAIL_HOST`
* `EMAIL_PORT`
* `EMAIL_HOST_USER`
* `EMAIL_HOST_PASSWORD`
* `EMAIL_TARGET`

# Handling requirements freeze

Using `./deploy.sh` on production usually runs rebulding python packages.

This can cause errors when there is a new version of a package that is required by "main" dependency (like `kombu` for `celery` https://stackoverflow.com/questions/50444988/celery-attributeerror-async-error). To prevent this `./app/src/requirements_freeze.py` script is provided. This script freezes `requirements.txt` using `pip freeze` on virtualenv, but keeps "main" depedencies separate from freezed ones (using `# -- pip freezed` comment). Additionally it scans "main" dependencies for their requirements and adds only those packages that are required by "main" dependecies.

This allows to run script in virtualenv with development packages installed (like `ipython`, `flake8`, `yapf` etc.).

To use `requirements_freeze.py` script just activate virtualenv, install packages using `pip install -r requirements.txt` and then run `./requirements_freeze.py`. It can take a while (even more than 60s) but it would not be run often.

To add new "main" dependecy to project, just install package using `pip` and add package to `requirements.txt` above `# -- pip freezed` comment with freezed version (`package-name==x.x.x`). Then run `requirements_freeze.py`.

To upgrade a package just upgrade it using `pip install --upgrade package-name` and then run `requirements_freeze.py` - script will update "main" package version in `requirements.txt` file.

There is one limitation - main dependecies needs to be provided with freezed version (`package-name==x.x.x`) - all other notation is considered "custom" dependecy (like github commit, etc.) and is processed without freezing version. Additionally if there is a match for package name in custom notation (eg. git+https://github.com/django-recurrence/django-recurrence.git@7c6fcdf26d96032956a14fc9cd6841ff931a52fe#egg=django-recurrence) then package depedencies are freezed (but custom package entry is left without change).

Notations like `package-name>=x.x.x` or `package-name` (without version) are considered custom and **should not be used** - all dependecies should be freezed - either by `requirements_freeze.py` script or by github commit/tag reference (or any equivalent - **branch reference is not freezing version**).

# Restoring system from backup after a catastrophical failure
1. Follow the instructions above to set up a new production environment
2. Restore the database using bin/restore-db.sh
3. See if everything works
4. Set up backups on the new machine
5. Make sure everything is filled up in .env, error reporting integration, email accounts etc
