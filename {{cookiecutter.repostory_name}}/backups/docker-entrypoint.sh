#!/bin/bash
set -eux
printenv > /etc/environment && cron && tail -f /var/log/cron.log &
uv run /root/serve_metrics.py