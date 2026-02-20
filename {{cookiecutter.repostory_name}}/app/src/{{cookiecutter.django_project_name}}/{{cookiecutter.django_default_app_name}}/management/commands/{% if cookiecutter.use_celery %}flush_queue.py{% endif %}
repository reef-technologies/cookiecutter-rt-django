from django.core.management.base import BaseCommand

from {{cookiecutter.django_project_name}}.celery import flush_tasks, get_num_tasks_in_queue


class Command(BaseCommand):
    help = "Flush task queue."

    def add_arguments(self, parser) -> None:
        parser.add_argument("queue", type=str, help="Queue name to flush")

    def handle(self, *args, **kwargs):
        queue_name = kwargs["queue"]

        num_tasks = get_num_tasks_in_queue(queue_name)
        self.stdout.write(f"Found {num_tasks} tasks in '{queue_name}' queue")
        if not num_tasks:
            return

        flush_tasks(queue_name)
        self.stdout.write("All done")
