import pytest
from django.contrib.auth.models import User

pytestmark = pytest.mark.django_db


def test__database__save_object():
    User(username="dummy", password="unhashed").save()
    assert User.objects.all().last().username == "dummy"
