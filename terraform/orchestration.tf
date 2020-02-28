### ECS

resource "aws_ecs_cluster" "main" {
  name = "${local.project}-ecs_cluster${local.name_suffix}"
}

resource "aws_ecs_task_definition" "default" {
  family       = "${local.project}${local.name_suffix}"
  network_mode = "awsvpc"
  requires_compatibilities = [
  "FARGATE"]
  cpu    = var.fargate_cpu
  memory = var.fargate_memory
  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn
  container_definitions = data.template_file.container_definition.rendered
}

resource "aws_ecs_service" "main" {
  name            = "${local.project}-ecs_service${local.name_suffix}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.default.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups = [aws_security_group.ecs_tasks.id]
    subnets         = data.terraform_remote_state.core.outputs.private_subnet_ids
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.default.arn
    container_name   = var.container_name
    container_port   = var.container_port
  }

  depends_on = [
    aws_lb_listener.default,
  ]
}


//#
//# ECS Resources
//#
//resource "aws_ecs_cluster" "default" {
//  name = "${local.project}-ecs_cluster${local.name_suffix}"
//}
//
//resource "aws_ecs_service" "default" {
//  name            =  "${local.project}-ecs_service${local.name_suffix}"
//  cluster         = aws_ecs_cluster.default.id
//  task_definition = aws_ecs_task_definition.default.arn
//
//  desired_count                      = var.desired_count
//  deployment_minimum_healthy_percent = var.deployment_min_percent
//  deployment_maximum_percent         = var.deployment_max_percent
//
//  launch_type = "FARGATE"
//
//  network_configuration {
//    security_groups = [aws_security_group.ecs_tasks.id]
//    subnets         = data.terraform_remote_state.core.outputs.public_subnet_ids
//    assign_public_ip = true # for public subnets only
//  }
//
//  load_balancer {
//    target_group_arn = aws_lb_target_group.default.arn
//    container_name   = var.container_name
//    container_port   = var.container_port
//  }
//
//  depends_on = [
//    aws_lb_listener.default,
//  ]
//}
//
//#
//# Task Definition
//#
//
//resource "aws_ecs_task_definition" "default" {
//  family                   = "${local.project}${local.name_suffix}"
//  network_mode             = "awsvpc"
//  requires_compatibilities = ["FARGATE"]
//  cpu                      = 256
//  memory                   = 512
//  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn
//  container_definitions = data.template_file.container_definition.rendered
//}