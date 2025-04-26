"""
This test file is here always to indicate that all dependencies were properly installed and the CI was able to run tests.
It also verifies if the healthcheck endpoint is functioning correctly
"""

from datetime import timedelta

import pytest
from django.utils.timezone import now
from freezegun import freeze_time


def test__setup(db, some):
    with freeze_time(now() - timedelta(days=1)):
        assert some == 1

    with pytest.raises(ZeroDivisionError):
        1 / 0


def test__alive_endpoint(client):
    response = client.get("/alive/")
    assert response.status_code == 200
