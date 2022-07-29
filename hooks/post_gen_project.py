#!/usr/bin/env python
import os

TO_REMOVE = [
{% if cookiecutter.monitoring == "n" or cookiecutter.use_constance == "n" %}
    "app/src/{{ cookiecutter.django_project_name }}/{{ cookiecutter.django_default_app_name }}/constance_prometheus.py",
{% endif %}
]

for path in TO_REMOVE:
    path = path.strip()
    if path and os.path.exists(path):
        os.unlink(path)
