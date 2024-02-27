from django.apps import AppConfig


class {{cookiecutter.django_default_app_name|title}}Config(AppConfig):
    name = "{{cookiecutter.django_project_name}}.{{cookiecutter.django_default_app_name}}"
