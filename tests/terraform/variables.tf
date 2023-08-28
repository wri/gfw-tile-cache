variable "lambda_edge_runtime" {
  description = "Runtime name and version (example: python3.10) for Lambda Edge"
  type        = string
  default     = "python3.9"
}

variable "lambda_runtime" {
  description = "Runtime name and version (example: python3.10)"
  type        = string
  default     = "python3.10"
}

variable "lambda_runtime_sn" {
  description = "Runtime name and version, short name (example: py310)"
  type        = string
  default     = "py310"
}