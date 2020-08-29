{% if cookiecutter.use_alpine_linux == "y" -%}
ARG BASE_IMAGE=python:3.8-alpine
{% else -%}
ARG BASE_IMAGE=python:3.8
{% endif %}

FROM $BASE_IMAGE AS base-image

WORKDIR /root/src/
ENV PATH=/root/.local/bin:$PATH

RUN pip3 install --user --no-cache-dir gunicorn==19.9.0

COPY ./src/requirements.txt requirements.txt

{% if cookiecutter.use_alpine_linux == "y" -%}
RUN grep psycopg2 requirements.txt && apk add --no-cache postgresql-dev gcc python3-dev musl-dev || true
RUN grep git:\/\/ requirements.txt && apk add --no-cache git || true
{% endif -%}

RUN pip3 install --user --no-cache-dir -r requirements.txt

COPY ./src/ /root/src/

RUN python3 -m compileall -b -f -q /root/
# By tricking these env variables we can run collectstatic during the container build.
# They aren't used by `collectstatic` so be fake.
RUN SECRET_KEY=0 CSP_ENABLED= DATABASE_URL= python3 manage.py collectstatic --no-input --clear


FROM $BASE_IMAGE AS secondary-image

WORKDIR /root/src/
ENV PYTHONUNBUFFERED=1
ENV PATH=/root/.local/bin:$PATH

COPY --from=base-image /root/ /root/

{% if cookiecutter.use_alpine_linux == "y" -%}
RUN grep psycopg2 requirements.txt && apk add --no-cache libpq || true
{% endif -%}

EXPOSE 8000

CMD ["./entrypoint.sh"]
