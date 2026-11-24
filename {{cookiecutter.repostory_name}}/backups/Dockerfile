FROM postgres:18.7@sha256:eb63372c1e05c755f55fa30cbd07aecc443676fc6c0fa90b9002d01537841e1a
WORKDIR /root
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=getsentry/sentry-cli:latest /bin/sentry-cli /bin/
RUN apt-get update && apt-get install -y cron zstd supervisor
COPY supervisord.conf /etc/supervisor/supervisord.conf
COPY --chmod=0644 cron.d/backup /etc/cron.d/backup
COPY bin ./
RUN uv venv && uv pip install -r requirements.txt

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]