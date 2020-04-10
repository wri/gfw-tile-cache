

data "aws_subnet" "public_subnet" {
  count = length(var.public_subnet_ids)
  id    = var.public_subnet_ids[count.index]
}

#
# ECS IAM resources
#
data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = [
      "sts:AssumeRole",
    ]
  }
}

data "template_file" "container_definition" {
  template = file("${path.root}/templates/container_definition.json.tmpl")
  vars = {
    image = "${var.repository_url}:latest"

    container_name = var.container_name
    container_port = var.container_port

    log_group = aws_cloudwatch_log_group.default.name

    //    postgresql_secret_arn = var.secrets_postgresql-reader_arn
    log_level   = var.log_level
    project     = var.project
    environment = var.environment
    aws_region  = var.region
  }
}

data "template_file" "autoscaling_role" {
  template = file("${path.root}/templates/service_role.json.tmpl")
  vars = {
    service = "ecs.application-autoscaling.amazonaws.com"
  }
}

data "local_file" "appautoscaling_role_policy" {

  filename = "${path.root}/templates/appautoscaling_role_policy.json"
}

