{%- if cookiecutter.monitoring == "y" -%}
import os
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

import psycopg2
from django.http import HttpRequest, HttpResponse, JsonResponse
from redis import Redis

from .models import HealthcheckModel


def check_orm(status: dict[str, Any]) -> bool:
    try:
        # delete all existing healthcheck records to prevent table bloat
        HealthcheckModel.objects.all().delete()

        # create and save a new healthcheck record
        obj = HealthcheckModel.objects.create(
            check_date=datetime.now(tz=UTC),
        )
        obj.save()

        status["orm_ok"] = True
        return True
    except Exception as e:
        status["orm_ok"] = False
        status["orm_error"] = repr(e)
        return False


def check_redis(status: dict[str, Any]) -> bool:
    try:
        redis = Redis(
            host=os.environ["REDIS_HOST"],
            port=int(os.environ["REDIS_PORT"]),
            socket_connect_timeout=1,
        )

        # echo test
        echo_test = str(datetime.now(tz=UTC)).encode("utf8")
        assert redis.echo(echo_test) == echo_test, "incorrect redis response"

        status["redis_ok"] = True
        return True
    except Exception as e:
        status["redis_ok"] = False
        status["redis_error"] = repr(e)
        return False


def check_postgres(status: dict[str, Any]) -> bool:
    try:
        with psycopg2.connect(
            dbname=os.environ["POSTGRES_DB"],
            host=os.environ["POSTGRES_HOST"],
            port=os.environ["POSTGRES_PORT"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 123")
                assert cur.fetchone()[0] == 123, "incorrect postgres response"

        status["postgres_ok"] = True
        return True
    except Exception as e:
        status["postgres_ok"] = False
        status["postgres_error"] = repr(e)
        return False


def healthcheck_view(_request: HttpRequest) -> HttpResponse:
    status: dict[str, Any] = {
        # include time so we can easily check if we receive a cached response
        "time": str(datetime.now(tz=UTC)),
    }

    all_ok = True
    all_ok &= check_postgres(status)
    all_ok &= check_redis(status)
    all_ok &= check_orm(status)
    status["all_ok"] = all_ok

    response = JsonResponse(status)
    response.status_code = HTTPStatus.OK if all_ok else HTTPStatus.INTERNAL_SERVER_ERROR
    return response
{% endif -%}
