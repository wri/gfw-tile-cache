variable "environment" {
  type        = string
  description = "An environment namespace for the infrastructure."
}

variable "region" {
  default = "us-east-1"
  type    = string
}
variable "container_name" {
  default     = "fire-vector-tiles"
  type        = string
  description = "The name of the container to associate with the load balancer."
}

variable "container_port" {
  default     = 80
  type        = number
  description = "The port on the container to associate with the load balancer."
}

variable "desired_count" {

  default     = 0
  type        = number
  description = "Number of tasks"
}

variable "deployment_min_percent" {


  default = 100
  type    = number
}
variable "deployment_max_percent" {


  default = 200
  type    = number
}

variable "fargate_cpu" {
  default = 256
  type    = number

}

variable "fargate_memory" {
  default = 512
  type    = number
}