#
# CloudWatch Resources
#
resource "aws_cloudwatch_log_group" "default" {
  name              = "/aws/ecs/${var.project}-log${var.name_suffix}"
  retention_in_days = 30
}


