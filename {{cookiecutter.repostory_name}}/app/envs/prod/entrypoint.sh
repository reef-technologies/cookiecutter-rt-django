#!/bin/sh

# We assume that WORKDIR is defined in Dockerfile

./manage.py wait_for_database

gunicorn --workers=4 --bind=0.0.0.0:8000 {% if cookiecutter.async == 'y' %}-k uvicorn.workers.UvicornWorker{% endif %} {{ cookiecutter.django_project_name }}.{% if cookiecutter.async == 'y' %}asgi{% else %}wsgi{% endif %}:application --access-logfile=-
