#!/bin/sh

# We assume that WORKDIR is defined in Dockerfile

{% if cookiecutter.monitoring == "y" %}[ "$PROMETHEUS_MULTIPROC_DIR" != "" -a -d "$PROMETHEUS_MULTIPROC_DIR" ] && rm -rf "$PROMETHEUS_MULTIPROC_DIR"/*{% endif %}
./manage.py wait_for_database --timeout 10

gunicorn -c gunicorn.conf.py
