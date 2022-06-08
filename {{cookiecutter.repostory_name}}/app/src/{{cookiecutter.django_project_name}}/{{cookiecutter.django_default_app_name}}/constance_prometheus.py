"""
Export django-constance variables as Prometheus metrics.

By default this module exports all constance variables which are of the ``int``,
``float``, ``bool`` or ``decimal.Decimal`` types and not included in the
``CONSTANCE_PROMETHEUS_BLACKLIST`` sequence.

The variables will appear named ``constance_config_VARIABLE_KEY`` and the numeric
types will be represented as Gauge metrics, while ``bool``s will turn into Enums.

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
from prometheus_client import REGISTRY, CollectorRegistry, Enum, Gauge

from . import metrics

__all__ = ("Metric", "on_constance_config_updated", "export_config")


def is_blacklisted(key):
    return key in getattr(settings, "CONSTANCE_PROMETHEUS_BLACKLIST", [])


def is_whitelisted(key):
    return key in getattr(settings, "CONSTANCE_PROMETHEUS_WHITELIST", [])


def gets_monitored(key, value):
    return not is_blacklisted(key) and (
        isinstance(value, (int, float, bool, Decimal)) or is_whitelisted(key)
    )


METRIC_NAME_FILTER = re.compile(r"\W", re.ASCII)


class Metric:
    prefix = "constance_config"
    config_key = None

    def __init__(self, config_key=None):
        self.config_key = config_key or self.config_key
        self.name = self._get_name()
        self.description = constance_settings.CONFIG[self.config_key][1]
        value = getattr(config, self.config_key)
        if isinstance(value, bool):
            self._metric = Enum(self.name, self.description, states=["true", "false"])
            self.store = lambda v: self._metric.state("true" if v else "false")
            return
        elif isinstance(value, (int, float, Decimal)):
            self._metric = Gauge(self.name, self.description)
            self.store = self._metric.set
            return
        else:
            # a str or custom type; cast everything to str
            value = str(value)
            self.name = self._get_name(value)
            self._metric = Gauge(self.name, self.description)
            self.store = self._store_str

    def _get_name(self, value=None):
        n = f"{self.prefix:s}_{self.config_key:s}"
        if value is not None:
            v = METRIC_NAME_FILTER.sub('_', value)
            n = f"{n}_{v}"
        return n

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


@receiver(config_updated)
def on_constance_config_updated(sender, key, old_value, new_value, **kwargs):
    if gets_monitored(key, new_value):
        if key not in METRICS:
            METRICS[key] = Metric(key)
        METRICS[key].store(new_value)


def export_config():
    for key in dir(config):
        value = getattr(config, key)
        if gets_monitored(key, value):
            if key not in METRICS:
                METRICS[key] = Metric(key)
            METRICS[key].store(value)


METRICS = {}
