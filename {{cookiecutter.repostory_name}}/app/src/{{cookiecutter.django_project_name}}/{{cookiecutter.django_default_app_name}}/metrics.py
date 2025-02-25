{%- if cookiecutter.monitoring == "y" -%}
import glob
import os
from collections.abc import Iterator

import prometheus_client
from django.conf import settings
from django.http import HttpResponse
from django_prometheus.exports import ExportToDjangoView
from prometheus_client import REGISTRY, multiprocess

from ..celery import num_tasks_in_queue, get_num_tasks_in_queue


class RecursiveMultiProcessCollector(multiprocess.MultiProcessCollector):
    """A multiprocess collector that scans the directory recursively"""

    def collect(self):
        files = glob.glob(os.path.join(self._path, "**/*.db"), recursive=True)
        return self.merge(files, accumulate=True)


if (is_multiprocess := bool(os.environ.get("PROMETHEUS_MULTIPROC_DIR"))):
    registry = prometheus_client.CollectorRegistry()
    RecursiveMultiProcessCollector(registry)
else:
    registry = REGISTRY


def metrics_view(request):
    """Exports metrics as a Django view"""

    for queue in settings.CELERY_TASK_QUEUES:
        num_tasks_in_queue.labels(queue.name).set(get_num_tasks_in_queue(queue.name))

    if is_multiprocess:
        return HttpResponse(
            prometheus_client.generate_latest(registry),
            content_type=prometheus_client.CONTENT_TYPE_LATEST,
        )

    return ExportToDjangoView(request)
{% endif %}