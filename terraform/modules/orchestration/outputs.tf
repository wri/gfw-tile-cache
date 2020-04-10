output "ecs_security_group_id" {
  value       = aws_security_group.ecs_tasks.id
  description = "Security group ID of the ECS service security group."
}

output "lb_dns_name" {
  value = aws_lb.default.dns_name
}