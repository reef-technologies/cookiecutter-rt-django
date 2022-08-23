#!/bin/sh

set -x

INSTANCE_TYPE_EC2=`wget http://169.254.169.254/latest/meta-data/instance-type -O- --timeout=5`
INSTANCE_TYPE="$(INSTANCE_TYPE_EC2:-UNKNOWN)"
cat << EOF > /home/nobody/textfile_collector_metrics/instance_type.prom
# HELP node_aws_ec2_instance_type type of ec2 instance
# TYPE node_aws_ec2_instance_type gauge
node_aws_ec2_instance_type{instance_type="$INSTANCE_TYPE"} 1
EOF

/bin/node_exporter --collector.textfile.directory=/home/nobody/textfile_collector_metrics/ "$@"