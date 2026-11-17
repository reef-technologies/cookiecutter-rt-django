#!/bin/bash
set -eux

{% if cookiecutter.deployment_type != 'aws' %}
rm -rf devops/tf devops/scripts
{% endif %}

find . -type d -empty -delete
uvx ruff format .
uvx ruff check --fix .
