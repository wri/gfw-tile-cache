# Require TF version to be same as or greater than 0.12.26
terraform {
  required_version = ">=0.12.26"
  backend "s3" {
    region  = "us-east-1"
    key     = "wri__gfw_fire-vector-tiles.tfstate"
    encrypt = true
  }
}

# Download any stable version in AWS provider of 2.65.0 or higher in 2.65 train
provider "aws" {
  region  = "us-east-1"
  version = "~> 2.70.0"
}

locals {
  name_suffix     = terraform.workspace == "default" ? "" : "-${terraform.workspace}"
  bucket_suffix   = var.environment == "production" ? "" : "-${var.environment}"
  tf_state_bucket = "gfw-terraform${local.bucket_suffix}"
  tags            = data.terraform_remote_state.core.outputs.tags
  project         = "gfw-tile-cache"
  container_tag   = substr(var.git_sha, 0, 7)
}


# Docker file for FastAPI app
module "container_registry" {
  source     = "git::https://github.com/wri/gfw-terraform-modules.git//terraform/modules/container_registry?ref=v0.2.6"
  image_name = lower("${local.project}${local.name_suffix}")
  root_dir   = "../${path.root}"
  tag        = local.container_tag
}


module "orchestration" {
  source                       = "git::https://github.com/wri/gfw-terraform-modules.git//terraform/modules/fargate_autoscaling?ref=v0.2.6"
  project                      = local.project
  name_suffix                  = local.name_suffix
  tags                         = local.tags
  vpc_id                       = data.terraform_remote_state.core.outputs.vpc_id
  private_subnet_ids           = data.terraform_remote_state.core.outputs.private_subnet_ids
  public_subnet_ids            = data.terraform_remote_state.core.outputs.public_subnet_ids
  container_name               = var.container_name
  container_port               = var.container_port
  desired_count                = var.desired_count
  fargate_cpu                  = var.fargate_cpu
  fargate_memory               = var.fargate_memory
  auto_scaling_cooldown        = var.auto_scaling_cooldown
  auto_scaling_max_capacity    = var.auto_scaling_max_capacity
  auto_scaling_max_cpu_util    = var.auto_scaling_max_cpu_util
  auto_scaling_min_capacity    = var.auto_scaling_min_capacity
  security_group_ids           = [data.terraform_remote_state.core.outputs.postgresql_security_group_id]
  task_role_policies           = []
  task_execution_role_policies = [data.terraform_remote_state.core.outputs.secrets_postgresql-reader_policy_arn]
  container_definition         = data.template_file.container_definition.rendered
}


module "content_delivery_network" {
  source             = "./modules/content_delivery_network"
  bucket_domain_name = module.storage.tiles_bucket_domain_name
  certificate_arn    = var.environment == "dev" ? null : data.terraform_remote_state.core.outputs.acm_certificate
  environment        = var.environment
  name_suffix        = local.name_suffix
  project            = local.project
  tags               = local.tags
  website_endpoint   = module.storage.tiles_bucket_website_endpoint
  tile_cache_app_url = module.orchestration.lb_dns_name
  log_retention      = var.log_retention
  tile_cache_url     = var.tile_cache_url
}

module "storage" {
  source                             = "./modules/storage"
  bucket_suffix                      = "${local.bucket_suffix}${local.name_suffix}"
  name_suffix                        = local.name_suffix
  cloudfront_access_identity_iam_arn = module.content_delivery_network.cloudfront_access_identity_iam_arn
  environment                        = var.environment
  lambda_edge_cloudfront_arn         = module.content_delivery_network.lambda_edge_cloudfront_arn
  tags                               = local.tags
  project                            = local.project
}