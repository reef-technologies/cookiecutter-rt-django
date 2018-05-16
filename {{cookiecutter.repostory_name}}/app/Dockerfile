FROM python:3.6

COPY ./bin/s6-overlay-amd64.tar.gz /tmp/s6-overlay-amd64.tar.gz

RUN tar xvfz /tmp/s6-overlay-amd64.tar.gz -C / \
    && rm -f /tmp/s6-overlay-amd64.tar.gz \
    && adduser --disabled-password --gecos '' celery

COPY ./src/ /srv/app/

WORKDIR /srv/app

RUN pip3 install --no-cache-dir -r requirements.txt gunicorn\
    && python3 -m compileall -b .

ENTRYPOINT ["/init"]

EXPOSE 8000

CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:8000", "{{ cookiecutter.django_project_name }}.wsgi:application"]
