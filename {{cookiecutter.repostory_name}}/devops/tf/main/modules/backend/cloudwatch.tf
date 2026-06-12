# Create the log group up front so the containers don't race each other on the
# first boot. With `awslogs-create-group: "true"` every service tries to call
# CreateLogGroup at the same time; the losers get OperationAbortedException and
# never start (and a driver-created group has no retention). Owning it here makes
# the group exist before any container boots and gives it a retention policy.
resource "aws_cloudwatch_log_group" "ec2" {
  name              = "/aws/ec2/${var.name}-${var.env}"
  retention_in_days = 30
}
