from django.core.management.base import BaseCommand
from {{cookiecutter.django_project_name}}.celery import move_tasks, get_num_tasks_in_queue


class Command(BaseCommand):
    help = 'Reschedule dead letter tasks.'

    def add_arguments(self, parser) -> None:
        parser.add_argument('source_queue', type=str, help='Source queue name')
        parser.add_argument('destination_queue', type=str, help='Destination queue name')

    def handle(self, *args, **kwargs):
        source_queue = kwargs['source_queue']
        destination_queue = kwargs['destination_queue']

        num_tasks = get_num_tasks_in_queue(source_queue)
        self.stdout.write(f'Found {num_tasks} tasks in "{source_queue}" queue')
        if not num_tasks:
            return

        move_tasks(source_queue, destination_queue)
        self.stdout.write('All done')
