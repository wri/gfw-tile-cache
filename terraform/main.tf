# Require TF version to be same as or greater than 0.12.13
terraform {
  required_version = ">=0.12.19"
  backend "s3" {
    region  = "us-east-1"
    key     = "wri__gfw_fire-vector-tiles.tfstate"
    encrypt = true
  }
}

# Download any stable version in AWS provider of 2.36.0 or higher in 2.36 train
provider "aws" {
  region  = "us-east-1"
  version = "~> 2.56.0"
}

# Docker file for FastAPI app
module "container_registry" {
  source     = "git::https://github.com/wri/gfw-terraform-modules.git//modules/container_registry?ref=v0.0.7"
  image_name = lower("${local.project}${local.name_suffix}")
  root_dir   = "../${path.root}"
}


module "orchestration" {
  source = "./modules/orchestration"

  environment = var.environment
  region      = var.region
  project     = local.project
  name_suffix = local.name_suffix
  tags        = local.tags

  vpc_id             = data.terraform_remote_state.core.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.core.outputs.private_subnet_ids
  public_subnet_ids  = data.terraform_remote_state.core.outputs.public_subnet_ids

  repository_url = module.container_registry.repository_url
  container_name = "gfw-tile-cache"
  container_port = 80
  desired_count  = 1

  deployment_min_percent = 100
  deployment_max_percent = 200
  fargate_cpu            = 256
  fargate_memory         = 2048
  log_level              = var.log_level

  auto_scaling_cooldown     = 300
  auto_scaling_max_capacity = 15
  auto_scaling_max_cpu_util = 75
  auto_scaling_min_capacity = 1

  postgresql_security_group_id         = data.terraform_remote_state.core.outputs.postgresql_security_group_id
  secrets_postgresql-reader_name        = data.terraform_remote_state.core.outputs.secrets_postgresql-reader_name
  secrets_postgresql-reader_policy_arn = data.terraform_remote_state.core.outputs.secrets_postgresql-reader_policy_arn
}


module "content_delivery_network" {
  source                              = "./modules/content_delivery_network"
  bucket_domain_name                  = module.storage.tiles_bucket_domain_name
  certificate_arn                     = var.environment == "production" ? data.terraform_remote_state.core.outputs.acm_certificate : null
//  cloudfront_access_identity_path     = data.terraform_remote_state.core.outputs.cloudfront_access_identity_path
  environment                         = var.environment
  project                             = local.project
  tags                                = local.tags
  website_endpoint                    = module.storage.tiles_bucket_website_endpoint
//  lambda_edge_cloudfront_iam_role_arn = data.terraform_remote_state.core.outputs.lambda_edge_cloudfront_arn
  tile_cache_app_url                  = module.orchestration.lb_dns_name
}

module "storage" {
  source = "./modules/storage"
  bucket_suffix = local.bucket_suffix
  cloudfront_access_identity_iam_arn = module.content_delivery_network.cloudfront_access_identity_iam_arn
  environment = var.environment
  lambda_edge_cloudfront_arn = module.content_delivery_network.lambda_edge_cloudfront_arn
  tags = local.tags
  project = local.project
}