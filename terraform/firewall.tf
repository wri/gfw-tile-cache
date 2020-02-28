# ALB Security group
# This is the group you need to edit if you want to restrict access to your application
resource "aws_security_group" "lb" {
  name        = "tf-ecs-alb"
  description = "controls access to the ALB"
  vpc_id      = data.terraform_remote_state.core.outputs.vpc_id

  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Traffic to the ECS Cluster should only come from the ALB
resource "aws_security_group" "ecs_tasks" {
  name        = "tf-ecs-tasks"
  description = "allow inbound access from the ALB only"
  vpc_id      = data.terraform_remote_state.core.outputs.vpc_id

  ingress {
    protocol        = "tcp"
    from_port       = var.container_port
    to_port         = var.container_port
    security_groups = [aws_security_group.lb.id]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

//#
//# Security Group Resources
//#
//resource "aws_security_group" "default" {
//  name   = "${local.project}-sgEcsService${local.name_suffix}"
//  vpc_id = data.terraform_remote_state.core.outputs.vpc_id
//
//  tags = merge(
//    {
//      Name        = "${local.project}-sgEcsService${local.name_suffix}" ,
//      Job     = local.project,
//    },
//    local.tags
//  )
//}
//
//resource "aws_security_group_rule" "ecs_https_egress" {
//  type             = "egress"
//  from_port        = 443
//  to_port          = 443
//  protocol         = "tcp"
//  cidr_blocks      = ["0.0.0.0/0"]
//  ipv6_cidr_blocks = ["::/0"]
//
//  security_group_id = aws_security_group.default.id
//}
//
//
//resource "aws_security_group_rule" "ecs_nlb_ingress" {
//  type        = "ingress"
//  from_port   = var.container_port
//  to_port     = var.container_port
//  protocol    = "tcp"
//  cidr_blocks = data.aws_subnet.public_subnet.*.cidr_block
//
//  security_group_id = aws_security_group.default.id
//}
//
//resource "aws_security_group_rule" "nlb_http_ingress" {
//  type             = "ingress"
//  from_port        = 80
//  to_port          = 80
//  protocol         = "tcp"
//  cidr_blocks      = ["0.0.0.0/0"]
//  ipv6_cidr_blocks = ["::/0"]
//
//  security_group_id = aws_security_group.default.id
//}