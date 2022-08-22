from datetime import timedelta

import pytest
from django.utils.timezone import now
from freezegun import freeze_time


def test_some(db, some):
    with freeze_time(now() - timedelta(days=1)):
        assert some == 1

    with pytest.raises(ZeroDivisionError):
        1 / 0
