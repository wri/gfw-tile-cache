output "cloudfront_distribution_domain_name" {
  value = module.content_delivery_network.cloudfront_distribution_domain_name
}

output "cloudfront_distribution_id" {
  value = module.content_delivery_network.cloudfront_distribution_id
}

output "tile_cache_bucket_name" {
  value = module.storage.tiles_bucket_name
}