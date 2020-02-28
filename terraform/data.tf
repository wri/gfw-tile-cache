data "terraform_remote_state" "core" {
  backend = "s3"
  config = {
    bucket = local.tf_state_bucket
    region = "us-east-1"
    key    = "core.tfstate"
  }
}

data "aws_subnet" "public_subnet" {
  count = length(data.terraform_remote_state.core.outputs.public_subnet_ids)
  id    = data.terraform_remote_state.core.outputs.public_subnet_ids[count.index]
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
  template = file("${path.module}/templates/container_definition.json.tmpl")
  vars = {
    image = "${module.container_registry.repository_url}:latest"

    container_name = var.container_name
    container_port = var.container_port

    log_group = aws_cloudwatch_log_group.default.name

    postgres_name     = "geostore"
    postgres_username = "gfw"
    postgres_password = "jxgFQb2$W83O$RbQ"
    postgres_host     = "gfw-postgres.cmwunwkcyxbz.us-east-1.rds.amazonaws.com"
    postgres_port     = 5432

    project     = local.project
    environment = var.environment
    aws_region  = var.region
  }
}