{%- if cookiecutter.monitoring == "y" -%}
import os
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from redis import Redis

from .models import HealthcheckModel


def check_database(status: dict[str, Any]) -> bool:
    try:
        # delete all existing healthcheck records to prevent table bloat
        HealthcheckModel.objects.all().delete()

        # create and save a new healthcheck record
        obj = HealthcheckModel.objects.create(
            check_date=datetime.now(tz=UTC),
        )
        obj.save()

        status["database_ok"] = True
        return True
    except Exception as e:
        status["database_ok"] = False
        status["database_error"] = repr(e)
        return False


def check_redis(status: dict[str, Any]) -> bool:
    try:
        redis_host = os.environ["REDIS_HOST"]
        redis_port = int(os.environ["REDIS_PORT"])
        redis = Redis(redis_host, redis_port, socket_connect_timeout=1)

        # echo test
        echo_test = str(datetime.now(tz=UTC)).encode("utf8")
        assert redis.echo(echo_test) == echo_test

        status["redis_ok"] = True
        return True
    except Exception as e:
        status["redis_ok"] = False
        status["redis_error"] = repr(e)
        return False


def healthcheck_view(_request: HttpRequest) -> HttpResponse:
    status = {}

    all_ok = True
    all_ok &= check_database(status)
    all_ok &= check_redis(status)
    status["all_ok"] = all_ok

    response = JsonResponse(status)
    response.status_code = HTTPStatus.OK if all_ok else HTTPStatus.INTERNAL_SERVER_ERROR
    return response
{% endif -%}
