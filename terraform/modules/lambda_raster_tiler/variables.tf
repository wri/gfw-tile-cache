variable "environment" { type = string }
variable "log_level" { type = string }
variable "log_retention" {
  default     = 30
  type        = number
  description = "Time in days to keep logs."
}
variable "source_dir" { type = string }
variable "lambda_layers" { type = list(string) }
variable "lambda_runtime" {
  type = string
  description = "Runtime name and version (example: python3.10)"
}
variable "project" { type = string }
variable "tags" { type = map(string) }
variable "data_lake_bucket_name" { type = string }
variable "tile_cache_url" { type = string }