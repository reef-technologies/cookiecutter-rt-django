#!/bin/bash
set -eux
touch /var/log/cron.log && cron && tail -f /var/log/cron.log &
uv run /root/serve_metrics.py