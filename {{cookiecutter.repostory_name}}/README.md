{{ cookiecutter.repostory_name }}
===============================

{{ cookiecutter.project_short_description }}

Skeleton of this project was generated with `cookiecutter-rt-django`, which sometimes gets upgrades that are easy to retrofit into already older projects.

Base requirements
-----------------

* docker
* docker-compose
* Python 3.8

For a fresh Ubuntu 20.04 you can install the above with:
```
$ sudo ./bin/prepare-os.sh
```

Setup development environment (virtualenv)
------------------------------------------

```
$ mkvirtualenv -p /usr/bin/python3.8 {{ cookiecutter.django_project_name }}
$ ./setup-dev.sh

# on second tab

$ docker-compose up

# then on first tab

$ cd app/src
$ python manage.py wait_for_database
$ python manage.py migrate
$ python manage.py runserver

```

Setup production environment (docker deployment)
------------------------------------------------

Use `ssh-keygen` to generate a key pair for the server, then add read-only access to repository in "deployment keys" section (`ssh -A` is easy to use, but not safe).

```
./setup-prod.sh

# change SECRET_KEY and (POSTGRES_PASSWORD or DATABASE_URL) in `.env`, adjust the rest of `.env` to your liking
{% if cookiecutter.use_https == 'y'%}
# set correct NGINX_HOSTNAME in .env for https

$ ./letsencrypt_setup.sh
{% endif %}
$ ./deploy.sh

```
{% if cookiecutter.use_https != 'y' %}
You've chosen http only project, but you can always add https - just set correct `NGINX_HOSTNAME` in `.env`
and uncomment lines in dc-prod.yml and nginx/conf/default.template and run
```
$ ./letsencrypt_setup.sh
```
{% endif %}

Setting up periodic backups
------------------

Add `cd {{ cookiecutter.repostory_name }}; {{ cookiecutter.repostory_name }}/bin/backup-db.sh` to crontab.

Set BACKUP_LOCAL_ROTATE_KEEP_LAST to keep only a specific number of most recent backups in local .backups directory.

### Configuring offsite targets for backups:

Backups are put in .backups directory locally, additionally then can be stored offsite in following ways:

#### Backblaze

Set BACKUP_B2_BUCKET_NAME, BACKUP_B2_KEY_ID, BACKUP_B2_KEY_SECRET in .env file

#### Email

Set EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_TARGET in .env file



Handling requirements freeze
----------------------------

Using `./deploy.sh` on production usually runs rebulding python packages.
This can cause errors when there is a new version of a package that is required
by "main" dependency (like `kombu` for `celery` https://stackoverflow.com/questions/50444988/celery-attributeerror-async-error). To prevent this `./app/src/requirements_freeze.py`
script is provided. This script freezes `requirements.txt` using `pip freeze`
on virtualenv, but keeps "main" depedencies separate from freezed ones (using
`# -- pip freezed` comment). Additionally it scans "main" dependencies for their
requirements and adds only those packages that are required by "main" dependecies.
This allows to run script in virtualenv with development packages installed (like
`ipython`, `flake8`, `yapf` etc.).

To use `requirements_freeze.py` script just activate virtualenv, install packages
using `pip install -r requirements.txt` and then run `./requirements_freeze.py`.
It can take a while (even more than 60s) but it would not be run often.

To add new "main" dependecy to project, just install package using `pip` and
add package to `requirements.txt` above `# -- pip freezed` comment with freezed
version (`package-name==x.x.x`). Then run `requirements_freeze.py`.

To upgrade a package just upgrade it using `pip install --upgrade package-name`
and then run `requirements_freeze.py` - script will update "main" package version
in `requirements.txt` file.

There is one limitation - main dependecies needs to be provided with freezed version
(`package-name==x.x.x`) - all other notation is considered "custom" dependecy
(like github commit, etc.) and is processed without freezing version. Additionally
if there is a match for package name in custom notation (eg. git+https://github.com/django-recurrence/django-recurrence.git@7c6fcdf26d96032956a14fc9cd6841ff931a52fe#egg=django-recurrence)
then package depedencies are freezed (but custom package entry is left without change).
Notations like `package-name>=x.x.x` or `package-name` (without version) are considered
custom and **should not be used** - all dependecies should be freezed - either by
`requirements_freeze.py` script or by github commit/tag reference
(or any equivalent - **branch reference is not freezing version**)

Restoring system from backup after a catastrophical failure
-----------------------------------------------------------
1. Follow the instructions above to set up a new production environment
2. Restore the database using bin/restore-db.sh
3. See if everything works
4. Set up backups on the new machine
5. Make sure everything is filled up in .env, error reporting integration, email accounts etc
