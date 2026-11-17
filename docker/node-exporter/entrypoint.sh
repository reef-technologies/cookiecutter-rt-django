#!/bin/sh

set -x

IMDS_HOST=169.254.169.254
INSTANCE_TYPE=''

# IMDSv2 (required on newer AMIs): busybox wget cannot send PUT, so get the session token with nc.
# Tracing is off while the token is around, to keep it out of the container logs.
set +x
TOKEN_RESPONSE=$(printf 'PUT /latest/api/token HTTP/1.0\r\nHost: %s\r\nX-aws-ec2-metadata-token-ttl-seconds: 60\r\n\r\n' "$IMDS_HOST" | nc -w 5 "$IMDS_HOST" 80)
case "$TOKEN_RESPONSE" in
  "HTTP/1."?" 200 "*)
    TOKEN=$(printf '%s' "$TOKEN_RESPONSE" | sed '1,/^\r*$/d')
    INSTANCE_TYPE=$(wget --header "X-aws-ec2-metadata-token: $TOKEN" "http://$IMDS_HOST/latest/meta-data/instance-type" -O- --timeout=5)
    ;;
esac
set -x

# IMDSv1 fallback
[ -z "$INSTANCE_TYPE" ] && INSTANCE_TYPE=$(wget "http://$IMDS_HOST/latest/meta-data/instance-type" -O- --timeout=5)
[ -z "$INSTANCE_TYPE" ] && INSTANCE_TYPE='UNKNOWN'

cat << EOF > /home/nobody/textfile_collector_metrics/instance_type.prom
# HELP node_aws_ec2_instance_type type of ec2 instance
# TYPE node_aws_ec2_instance_type gauge
node_aws_ec2_instance_type{instance_type="$INSTANCE_TYPE"} 1
EOF

exec /bin/node_exporter --collector.textfile.directory=/home/nobody/textfile_collector_metrics/ "$@"
