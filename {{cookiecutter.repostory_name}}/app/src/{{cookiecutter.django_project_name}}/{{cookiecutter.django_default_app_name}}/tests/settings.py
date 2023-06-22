import os

os.environ.update({
    "DEBUG_TOOLBAR": "False",
})

from {{cookiecutter.django_project_name}}.settings import *  # noqa: E402,F403
{% if cookiecutter.monitoring == "y" %}
PROMETHEUS_EXPORT_MIGRATIONS = False
{%- endif %}
