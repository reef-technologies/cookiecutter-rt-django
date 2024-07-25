{%- if cookiecutter.use_celery == 'y' -%}
import structlog
from celery import Task
from celery.utils.log import get_task_logger

from {{cookiecutter.django_project_name}}.celery import app

logger = structlog.wrap_logger(get_task_logger(__name__))


def send_to_dead_letter_queue(task: Task, exc, task_id, args, kwargs, einfo):
    """
    Hook to put a task into dead letter queue when it fails.

    The task should be annotated with `on_failure=send_to_dead_letter_queue`.
    Once the reason of tasks failure is fixed, the task can be re-processed
    by running a worker on dead letter queue:

        celery -A mrc.celery worker -Q dead_letter

    If tasks fails again, it will be put back to dead letter queue. This can
    potentially create an infinite loop, so make sure to fix the reason of
    failure before re-processing the task, or stop the worker after a few
    retries. The process of re-processing tasks is supposed to be manual,
    thus there are no complicated mechanisms to prevent infinite loops.
    """
    if task.app.conf.task_always_eager:
        return  # do not run failed task again in eager mode

    logger.warning(
        "Sending failed task to dead letter queue",
        task=task, exc=exc, task_id=task_id, args=args, kwargs=kwargs, einfo=einfo,
    )
    task.apply_async(args=args, kwargs=kwargs, queue='dead_letter')


@app.task(on_failure=send_to_dead_letter_queue)
def demo_task(x, y):
    logger.info("adding two numbers", x=x, y=y)
    return x + y
{% endif %}