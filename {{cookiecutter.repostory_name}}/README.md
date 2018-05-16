{{ cookiecutter.repostory_name }}
===============================

{{ cookiecutter.project_short_description }}

Requirements
------------

* docker
* docker-compose
* direnv (https://direnv.net/ - installation and setup instruction)
* Python 3.6

Setup virtualenv
----------------

```
$ mkvirtualenv -p /usr/bin/python3.6 {{ cookiecutter.django_project_name }}
$ ./setup-virtualenv.sh

# on second tab

$ docker-compose up

# wait till db is initialized, then on first tab

$ cd app/src
$ python manage.py migrate
$ python manage.py runserver

```

Setup production docker deployment
----------------------------------

```
./setup-docker-prod.sh

# change SECRET_KEY and POSTGRES_PASSWORD in .env !!!

$ docker-compose up

# wait till db is initialized then Ctrl + C

$ ./deploy.sh

```
