from {{cookiecutter.django_project_name}}.settings import *  # noqa: F403

DEBUG_TOOLBAR = False
{%- if cookiecutter.monitoring == "y" %}
PROMETHEUS_EXPORT_MIGRATIONS = False
{%- endif %}
