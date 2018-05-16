from celery.utils.log import get_task_logger

from {{cookiecutter.django_project_name}}.celery import app

logger = get_task_logger(__name__)
