#!/bin/sh

# We assume that WORKDIR is defined in Dockerfile

./manage.py wait_for_database --timeout 10

gunicorn --workers=4 --bind=0.0.0.0:8000 {{ cookiecutter.django_project_name }}.wsgi:application --access-logfile=-
