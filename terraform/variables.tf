variable "environment" {
  type        = string
  description = "An environment namespace for the infrastructure."
}

variable "region" {
  default = "us-east-1"
  type    = string
}

variable "log_level" {
  type = string
}

variable "container_name" {
  default = "gfw-tile-cache"
  type    = string
}

variable "container_port" {
  default = 80
  type    = number
}

variable "desired_count" {
  default = 1
  type    = number
}

variable "log_retention" {
  default = 30
  type    = number
}