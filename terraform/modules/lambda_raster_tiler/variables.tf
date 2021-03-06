variable "environment" { type = string }
variable "log_level" { type = string }
variable "log_retention" {
  default     = 30
  type        = number
  description = "Time in days to keep logs."
}
variable "source_dir" { type = string }
variable "lambda_layers" { type = list(string) }
variable "project" { type = string }
variable "tags" { type = map(string) }