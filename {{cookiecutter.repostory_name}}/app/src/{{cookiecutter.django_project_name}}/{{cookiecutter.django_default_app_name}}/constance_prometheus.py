"""
Export django-constance variables as Prometheus metrics.

By default this module exports all constance variables which are of the ``int``,
``float``, ``bool`` or ``decimal.Decimal`` types and not included in the
``CONSTANCE_PROMETHEUS_BLACKLIST`` sequence.

The variables will appear named ``constance_config_VARIABLE_KEY`` and represented
as Gauge metrics.

The ``CONSTANCE_PROMETHEUS_WHITELIST`` sequence may specify additional variables
to be exported. Their values will be cast into ``str`` and appended to the metric
name (e.g. ``VAR="foo bar"`` will become ``constance_config_VAR_foo_bar``) and
get 1.0 value. Once changed, the old metric becomes 0.0 and new one will appear,
allowing to present different values on a graph.

"""
import os
import re

from constance import config, settings as constance_settings
from constance.signals import config_updated
from decimal import Decimal
from django.conf import settings
from django.dispatch import receiver
from prometheus_client import REGISTRY, CollectorRegistry, Gauge

from . import metrics


def is_blacklisted(key):
    return key in getattr(settings, "CONSTANCE_PROMETHEUS_BLACKLIST", [])


def is_whitelisted(key):
    return key in getattr(settings, "CONSTANCE_PROMETHEUS_WHITELIST", [])


def is_of_automatically_monitored_type(value):
    return isinstance(value, (int, float, bool, Decimal))


def gets_monitored(key, value):
    return not is_blacklisted(key) and (
        is_of_automatically_monitored_type(value) or is_whitelisted(key)
    )


METRIC_NAME_FILTER = re.compile(r"\W", re.ASCII)


class Metric:
    PREFIX = "constance_config"

    def __init__(self, config_key):
        self.config_key = config_key
        self.name = self._get_name()
        self.description = constance_settings.CONFIG[self.config_key][1]
        value = getattr(config, self.config_key)
        if is_of_automatically_monitored_type(value):
            self._metric = Gauge(self.name, self.description)
            self.store = self._metric.set
        else:
            # a str or custom type; cast everything to str
            value = str(value)
            self.name = self._get_name(value)
            self._metric = Gauge(self.name, self.description)
            self.store = self._store_str

    def _get_name(self, value=None):
        name_candidate = f"{self.PREFIX:s}_{self.config_key:s}"
        if value is not None:
            alnum_value = METRIC_NAME_FILTER.sub("_", value)
            name_candidate = f"{name_candidate}_{alnum_value}"
        return name_candidate

    def _unregister(self):
        if os.environ.get(metrics.ENV_VAR_NAME):
            registry = CollectorRegistry()
            metrics.RecursiveMultiProcessCollector(registry)
        else:
            registry = REGISTRY
        try:
            # NOTE: This will fail in multiprocess mode
            registry.unregister(self._metric)
        except KeyError:
            # FIXME: Once unregistering fails, the metric remains in the registry.
            # As the value of string variables is converted to the metric name,
            # returning to previous setting may cause duplicates to appear.
            pass

    def _store_str(self, value):
        value = str(value)
        name = self._get_name(value)
        if name == self.name:
            self._metric.set(1)
            return
        else:
            self._metric.set(0)
        # the value has changed, so we change the name
        # first, unregister the old metric to avoid duplicating when old value is set
        self._unregister()
        self.name = name
        self._metric = Gauge(self.name, self.description)
        self._metric.set(1)


def _update_metric_if_needed(key, new_value):
    if gets_monitored(key, new_value):
        if key not in METRICS:
            METRICS[key] = Metric(key)
        METRICS[key].store(new_value)


@receiver(config_updated)
def on_constance_config_updated(sender, key, old_value, new_value, **kwargs):
    _update_metric_if_needed(key, new_value)


def export_config():
    for key in dir(config):
        value = getattr(config, key)
        _update_metric_if_needed(key, value)


METRICS = {}
