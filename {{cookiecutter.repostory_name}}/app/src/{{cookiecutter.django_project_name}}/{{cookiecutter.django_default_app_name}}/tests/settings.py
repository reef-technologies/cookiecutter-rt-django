import os

from {{cookiecutter.django_project_name}}.settings import *  # noqa: E402,F403

os.environ["DEBUG_TOOLBAR"] = "False"

{% if cookiecutter.monitoring == "y" %}
PROMETHEUS_EXPORT_MIGRATIONS = False
{% endif %}
