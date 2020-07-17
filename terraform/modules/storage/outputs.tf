output "tiles_bucket_domain_name" {
  value = aws_s3_bucket.tiles.bucket_domain_name
}

output "tiles_bucket_website_endpoint" {
  value = aws_s3_bucket.tiles.website_endpoint
}

output "tiles_bucket_name" {
  value = aws_s3_bucket.tiles.id
}

output "tile_bucket_policy_update_policy_arn" {
  value = aws_iam_policy.s3_update_bucket_policy.arn
}