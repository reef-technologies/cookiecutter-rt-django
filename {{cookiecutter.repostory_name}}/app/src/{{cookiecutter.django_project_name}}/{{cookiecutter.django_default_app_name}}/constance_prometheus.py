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
import re

from constance import config, settings as constance_settings
from constance.signals import config_updated
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from django.conf import settings
from django.dispatch import receiver
from prometheus_client import REGISTRY, Gauge
from typing import Any


def is_blacklisted(key: str) -> bool:
    return key in getattr(settings, "CONSTANCE_PROMETHEUS_BLACKLIST", [])


def is_whitelisted(key: str) -> bool:
    return key in getattr(settings, "CONSTANCE_PROMETHEUS_WHITELIST", [])


def is_of_automatically_monitored_type(value: Any) -> bool:
    return isinstance(
        value, (int, float, bool, Decimal, datetime, date, time, timedelta)
    )


def gets_monitored(key: str, value: Any) -> bool:
    return not is_blacklisted(key) and (
        is_of_automatically_monitored_type(value) or is_whitelisted(key)
    )


METRIC_NAME_FILTER = re.compile(r"\W", re.ASCII)


class Metric:
    PREFIX = "constance_config"

    def __init__(self, config_key: str):
        self.config_key = config_key
        self.name = self._get_name()
        self.description = constance_settings.CONFIG[self.config_key][1]
        value = getattr(config, self.config_key)
        if is_of_automatically_monitored_type(value):
            self._metric = Gauge(self.name, self.description)
            if isinstance(value, datetime):
                self.store = self._store_datetime
            elif isinstance(value, date):
                self.store = self._store_date
            elif isinstance(value, time):
                self.store = self._store_time
            elif isinstance(value, timedelta):
                self.store = self._store_timedelta
            else:
                self.store = self._metric.set
        else:
            # a str or custom type; cast everything to str
            value = str(value)
            self.name = self._get_name(value)
            self._metric = self._recycle_str()
            self.store = self._store_str

    def _get_name(self, value: Any = None) -> str:
        name_candidate = f"{self.PREFIX:s}_{self.config_key:s}"
        if value is not None:
            alnum_value = METRIC_NAME_FILTER.sub("_", value)
            name_candidate = f"{name_candidate}_{alnum_value}"
        return name_candidate

    def _recycle_str(self):
        try:
            return REGISTRY._names_to_collectors[self.name]
        except KeyError:
            pass
        return Gauge(self.name, self.description)

    def _store_datetime(self, value: datetime):
        if value.tzinfo:
            # convert to UTC and make TZ-naive
            value = (value - value.utcoffset()).replace(tzinfo=None)
        self._metric.set(int(value.timestamp()))

    def _store_date(self, value: date):
        self._store_datetime(datetime(value.year, value.month, value.day))

    def _store_time(self, value: time):
        self._metric.set(value.hour * 60 * 60 + value.minute * 60 + value.second)

    def _store_timedelta(self, value: timedelta):
        self._metric.set(int(value.total_seconds()))

    def _store_str(self, value: Any):
        value = str(value)
        name = self._get_name(value)
        if name == self.name:
            self._metric.set(1)
            return
        else:
            self._metric.set(0)
        self.name = name
        self._metric = self._recycle_str()
        self._metric.set(1)


def store_monitored_metric(key: str, new_value: Any):
    """
    Stores a single ``key = value`` pair, if among monitored variables.
    """
    if gets_monitored(key, new_value):
        if key not in METRICS:
            METRICS[key] = Metric(key)
        METRICS[key].store(new_value)


def store_monitored():
    """
    Stores all monitored config variables into metrics.
    """
    for key in dir(config):
        value = getattr(config, key)
        store_monitored_metric(key, value)


METRICS = {}


@receiver(config_updated)
def on_constance_config_updated(sender, key, old_value, new_value, **kwargs):
    store_monitored_metric(key, new_value)
