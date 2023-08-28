variable "lambda_edge_runtime" {
  description = "Runtime name and version (example: python3.9) for Lambda Edge"
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
  default     = replace(replace(var.lambda_runtime, ".", ""), "thon")
}

variable "mercantile_name_version" {
  description = "Name and version, separated by underscore (example: mercantile_1.2.1)"
  type        = string
  default     = "mercantile_1.2.1"
}

variable "pillow_name_version" {
  description = "Name and version, separated by underscore (example: pillow_9.5.0)"
  type        = string
  default     = "pillow_9.5.0"
}

variable "rasterio_name_version" {
  description = "Name and version, separated by underscore (example: rasterio_1.3.8)"
  type        = string
  default     = "rasterio_1.3.8"
}