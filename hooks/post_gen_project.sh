#!/bin/bash
set -eux

{% if cookiecutter.deployment_type != 'aws' %}
rm -rf devops/tf devops/packer devops/scripts
{% endif %}

{% if cookiecutter.deployment_type != 'vultr' %}
rm -rf devops/vultr_tf devops/vultr_scripts
{% endif %}

find . -type d -empty -delete
uvx ruff format .
uvx ruff check --fix .
