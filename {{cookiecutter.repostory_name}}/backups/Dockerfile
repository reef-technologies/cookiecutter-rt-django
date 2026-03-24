FROM postgres:17
WORKDIR /root
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=getsentry/sentry-cli:latest /bin/sentry-cli /bin/
RUN apt-get update && apt-get install -y cron zstd supervisor
COPY supervisord.conf /etc/supervisor/supervisord.conf
COPY --chmod=0644 cron.d/backup /etc/cron.d/backup
COPY bin ./
RUN uv venv && uv pip install -r requirements.txt

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]