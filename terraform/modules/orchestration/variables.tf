variable "environment" {
  type        = string
  description = "An environment namespace for the infrastructure."
}

variable "region" {
  type = string
}
variable "project" {
  type = string
}

variable "name_suffix" {
  type = string
}

variable "tags" {
  type = map(string)
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "repository_url" {
  type = string
}
variable "container_name" {
  type        = string
  description = "The name of the container to associate with the load balancer."
}

variable "container_port" {
  type        = number
  description = "The port on the container to associate with the load balancer."
}

variable "desired_count" {
  type        = number
  description = "Number of tasks"
}

variable "deployment_min_percent" {
  type = number
}

variable "deployment_max_percent" {
  type = number
}

variable "fargate_cpu" {
  type = number
}

variable "fargate_memory" {
  type = number
}

variable "log_level" {
  type = string
}

variable "auto_scaling_max_cpu_util" {
  type = number
}

variable "auto_scaling_max_capacity" {
  type = number
}

variable "auto_scaling_min_capacity" {
  type = number
}

variable "auto_scaling_cooldown" {
  type = number
}

variable "postgresql_security_group_id" {
  type = string
}

variable "secrets_postgresql-reader_policy_arn" {
  type = string
}

variable "secrets_postgresql-reader_arn" {
  type = string
}