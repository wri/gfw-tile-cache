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

output "ecs_update_service_policy_arn" {
  value = module.orchestration.ecs_update_service_policy_arn
}

output "tile_cache_bucket_write_policy_arn" {
  value = module.storage.s3_write_tiles_arn
}

output "tile_cache_bucket_full_access_policy_arn" {
  value = module.storage.s3_full_access_tiles_arn
}