variable "project" {}
variable "name_suffix" {}
variable "tags" {}
variable "environment" {}
variable "certificate_arn" {}
variable "bucket_domain_name" {}
variable "website_endpoint" {}
variable "lambda_edge_runtime" {
  type = string
  description = "Runtime name and version (example: python3.9)"
}
//variable "cloudfront_access_identity_path" {}
//variable "lambda_edge_cloudfront_iam_role_arn" {}
variable "tile_cache_app_url" {}
variable "log_retention" {}
variable "tile_cache_url" {}