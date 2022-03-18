#!/bin/sh

# We assume that WORKDIR is defined in Dockerfile

{% if cookiecutter.monitoring == "y" %}rm -r "$PROMETHEUS_MULTIPROC_DIR/*"{% endif %}
./manage.py wait_for_database --timeout 10

gunicorn -c gunicorn.conf.py
