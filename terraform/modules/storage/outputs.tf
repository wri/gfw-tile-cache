output "tiles_bucket_domain_name" {
  value = aws_s3_bucket.tiles.bucket_domain_name
}

output "tiles_bucket_website_endpoint" {
  value = aws_s3_bucket.tiles.website_endpoint
}

output "tiles_bucket_name" {
  value = aws_s3_bucket.tiles.id
}
