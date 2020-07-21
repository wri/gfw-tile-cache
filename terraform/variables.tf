variable "environment" {
  type        = string
  description = "An environment namespace for the infrastructure."
}

variable "region" {
  default     = "us-east-1"
  type        = string
  description = "Default AWS Region."
}

variable "log_level" {
  type    = string
  default = "Log level for tile service app."
}

variable "container_name" {
  default     = "gfw-tile-cache"
  type        = string
  description = "Description of tile service app container image."
}

variable "container_port" {
  default     = 80
  type        = number
  description = "Port tile cache app will listen on."

}

variable "desired_count" {
  type        = number
  description = "Initial number of service instances to launch."
}

variable "log_retention" {
  default     = 30
  type        = number
  description = "Time in days to keep logs."
}

variable "git_sha" {
  type        = string
  description = "Git SHA to use to tag image."
}

variable "tile_cache_url" {
  type        = string
  description = "URL of tile cache."
}

variable "auto_scaling_min_capacity" {
  type        = number
  description = "Minimum number of tasks to keep when scaling down."
}

variable "auto_scaling_max_capacity" {
  type        = number
  description = "Minimum number of tasks to deploy when scaling up."
}

variable "fargate_cpu" {
  default     = 256
  type        = number
  description = "vCPU for service."
}
variable "fargate_memory" {
  default     = 1024
  type        = number
  description = "Memory for service in MB."
}
variable "auto_scaling_cooldown" {
  default     = 300
  type        = number
  description = "Time in seconds to pass before scaling up or down again."
}
variable "auto_scaling_max_cpu_util" {
  default     = 75
  type        = number
  description = "CPU usage percentage which will trigger autoscaling event."
}