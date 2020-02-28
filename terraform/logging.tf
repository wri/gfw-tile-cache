#
# CloudWatch Resources
#
resource "aws_cloudwatch_log_group" "default" {
  name              = "${local.project}-log${local.name_suffix}"
  retention_in_days = 30
}


