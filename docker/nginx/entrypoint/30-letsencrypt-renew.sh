#!/bin/sh

[ -f "/usr/bin/certbot" ] || exit 0;

cron_dir=""

[ -d "/etc/periodic/daily/" ] && cron_dir="/etc/periodic/daily";
[ -d "/etc/cron.daily" ] && cron_dir="/etc/cron.daily";
[ ! "$cron_dir" = "" ] || exit 0;

certbot_file="${cron_dir}/certbot"
echo "Installing Let's Encrypt crontab script into $certbot_file"
echo "certbot -q --nginx renew" > "$certbot_file"
chmod +x "$certbot_file"

echo "Running certbot renew on startup..."
certbot --nginx renew