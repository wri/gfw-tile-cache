output "cloudfront_distribution_domain_name" {
  value = aws_cloudfront_distribution.tiles.domain_name
}

output "cloudfront_access_identity_path" {
  value       = aws_cloudfront_origin_access_identity.tiles.cloudfront_access_identity_path
  description = "Path of Cloud Front Origin Access Identity"
}

output "cloudfront_access_identity_iam_arn" {
  value       = aws_cloudfront_origin_access_identity.tiles.iam_arn
  description = "IAM ARN of Cloud Front Origin Access Identity"
}

output "lambda_edge_cloudfront_arn" {
  value = aws_iam_role.lambda_edge_cloudfront.arn
}


output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.tiles.id
}

output "tile_cache_url" {
  value = "https://${local.tile_cache_url}"
}