output "cloudfront_distribution_domain_name" {
  value = module.content_delivery_network.cloudfront_distribution_domain_name
}

output "cloudfront_distribution_id" {
  value = module.content_delivery_network.cloudfront_distribution_id
}

output "tile_cache_bucket_name" {
  value = module.storage.tiles_bucket_name
}

output "tile_cache_url" {
  value = "https://${var.tile_cache_url}"
}

output "tile_cache_cluster" {
  value = module.orchestration.ecs_cluster_name
}

output "tile_cache_service" {
  value = module.orchestration.ecs_service_name
}