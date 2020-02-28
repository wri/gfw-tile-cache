
#
# NLB Resources
#
resource "aws_lb" "default" {
  name = substr("${local.project}-loadbalancer${local.name_suffix}", 0, 32)
  //  internal                         = true
  //  load_balancer_type               = "network"
  enable_cross_zone_load_balancing = true

  subnets         = data.terraform_remote_state.core.outputs.public_subnet_ids
  security_groups = [aws_security_group.lb.id]

  tags = merge(
    {
      Job = local.project,
    },
    local.tags
  )
}

resource "aws_lb_target_group" "default" {
  name = substr("${local.project}-TargetGroup${local.name_suffix}", 0, 32)
  //
  //  health_check {
  //    protocol          = "TCP"
  //    interval          = "30"
  //    healthy_threshold = "3"
  //    # For Network Load Balancers, this value must be the same as the healthy_threshold.
  //    unhealthy_threshold = "3"
  //  }

  port = "80"
  //  protocol = "TCP"
  protocol = "HTTP"
  vpc_id   = data.terraform_remote_state.core.outputs.vpc_id

  target_type = "ip"

  tags = merge(
    {
      Job = local.project,
    },
    local.tags
  )
}

resource "aws_lb_listener" "default" {
  load_balancer_arn = aws_lb.default.id
  port              = "80"
  //  protocol          = "TCP"
  protocol = "HTTP"
  default_action {
    target_group_arn = aws_lb_target_group.default.id
    type             = "forward"
  }
}