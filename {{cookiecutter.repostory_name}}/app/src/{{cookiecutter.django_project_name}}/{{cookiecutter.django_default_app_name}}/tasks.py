{%- if cookiecutter.use_celery == "y" -%}
import structlog
from celery import Task
from celery.utils.log import get_task_logger

from {{cookiecutter.django_project_name}}.celery import app

logger = structlog.wrap_logger(get_task_logger(__name__))


def send_to_dead_letter_queue(task: Task, exc, task_id, args, kwargs, einfo):
    """Hook to put a task into dead letter queue when it fails."""
    if task.app.conf.task_always_eager:
        return  # do not run failed task again in eager mode

    logger.warning(
        "Sending failed task to dead letter queue",
        task=task,
        exc=exc,
        task_id=task_id,
        args=args,
        kwargs=kwargs,
        einfo=einfo,
    )
    task.apply_async(args=args, kwargs=kwargs, queue="dead_letter")


@app.task(on_failure=send_to_dead_letter_queue)
def demo_task(x, y):
    logger.info("adding two numbers", x=x, y=y)
    return x + y
{% endif %}