variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "bucket_suffix" {
  type = string
}

variable "tags" {
  type = map(string)
}

variable "cloudfront_access_identity_iam_arn" {
  type = string
}

variable "lambda_edge_cloudfront_arn" {
  type = string
}