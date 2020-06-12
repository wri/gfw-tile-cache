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
  version = "~> 2.65.0"
}

locals {
  name_suffix     = terraform.workspace == "default" ? "" : "-${terraform.workspace}"
  bucket_suffix   = var.environment == "production" ? "" : "-${var.environment}"
  tf_state_bucket = "gfw-terraform${local.bucket_suffix}"
  tags            = data.terraform_remote_state.core.outputs.tags
  project         = "gfw-tile-cache"

}


# Docker file for FastAPI app
module "container_registry" {
  source     = "git::https://github.com/wri/gfw-terraform-modules.git//modules/container_registry?ref=v0.1.5"
  image_name = lower("${local.project}${local.name_suffix}")
  root_dir   = "../${path.root}"
}


module "orchestration" {
  source                       = "git::https://github.com/wri/gfw-terraform-modules.git//modules/fargate_autoscaling?ref=v0.1.5"
  project                      = local.project
  name_suffix                  = local.name_suffix
  tags                         = local.tags
  vpc_id                       = data.terraform_remote_state.core.outputs.vpc_id
  private_subnet_ids           = data.terraform_remote_state.core.outputs.private_subnet_ids
  public_subnet_ids            = data.terraform_remote_state.core.outputs.public_subnet_ids
  container_name               = var.container_name
  container_port               = var.container_port
  desired_count                = var.desired_count
  fargate_cpu                  = 256
  fargate_memory               = 2048
  auto_scaling_cooldown        = 300
  auto_scaling_max_capacity    = 15
  auto_scaling_max_cpu_util    = 75
  auto_scaling_min_capacity    = 1
  security_group_ids           = [data.terraform_remote_state.core.outputs.postgresql_security_group_id]
  task_role_policies           = []
  task_execution_role_policies = [data.terraform_remote_state.core.outputs.secrets_postgresql-reader_policy_arn]
  container_definition         = data.template_file.container_definition.rendered
}


module "content_delivery_network" {
  source             = "./modules/content_delivery_network"
  bucket_domain_name = module.storage.tiles_bucket_domain_name
  certificate_arn    = var.environment == "production" ? data.terraform_remote_state.core.outputs.acm_certificate : null
  environment        = var.environment
  name_suffix        = local.name_suffix
  project            = local.project
  tags               = local.tags
  website_endpoint   = module.storage.tiles_bucket_website_endpoint
  tile_cache_app_url = module.orchestration.lb_dns_name
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