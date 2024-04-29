output "tiles_bucket_domain_name" {
  value = aws_s3_bucket.tiles.bucket_domain_name
}

output "tiles_bucket_website_endpoint" {
  value = aws_s3_bucket.tiles.website_endpoint
}

output "tiles_bucket_name" {
  value = aws_s3_bucket.tiles.id
}

output "tiles_bucket_arn" {
  value = aws_s3_bucket.tiles.arn
}

output "s3_write_tiles_arn" {
  value = aws_iam_policy.s3_write_tiles.arn
}

output "s3_full_access_tiles_arn" {
  value = aws_iam_policy.s3_full_access_tiles.arn
}