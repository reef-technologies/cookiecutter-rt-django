FROM postgres:17
WORKDIR /root
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=getsentry/sentry-cli:latest /bin/sentry-cli /bin/
RUN apt-get update && apt-get install -y python3.11 cron zstd
COPY docker-entrypoint.sh /
COPY --chmod=0644 backup.cron /etc/cron.d/backup
COPY bin ./
RUN uv venv .venv && uv pip install -r requirements.txt

CMD ["/docker-entrypoint.sh"]