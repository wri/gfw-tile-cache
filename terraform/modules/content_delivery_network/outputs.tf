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