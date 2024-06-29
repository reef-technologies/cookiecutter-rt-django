import pytest
from django.db import models

pytestmark = pytest.mark.django_db


class DummyValue(models.Model):
    value = models.IntegerField()


def test__database__save_object():
    DummyValue(value=42).save()
    assert DummyValue.objects.get().value == 42
