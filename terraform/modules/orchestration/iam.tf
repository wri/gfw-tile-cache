resource "aws_iam_role" "ecs_task_execution_role" {
  name               = "${var.project}-ECS_TaskExecutionRole${var.name_suffix}"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  name               = "${var.project}-ECS_TaskRole${var.name_suffix}"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = var.secrets_postgresql-reader_policy_arn
}

resource "aws_iam_role" "autoscaling" {
  name               = "${var.project}-appautoscaling-role${var.name_suffix}"
  assume_role_policy = data.template_file.autoscaling_role.rendered
}

resource "aws_iam_role_policy" "autoscaling" {
  name   = "${var.project}-appautoscaling-policy${var.name_suffix}"
  policy = data.local_file.appautoscaling_role_policy.content
  role   = aws_iam_role.autoscaling.id
}