terraform {
  backend "s3" {
    region  = "us-east-1"
    key     = "wri__gfw_fire-vector-tiles.tfstate"
    encrypt = true
  }
}


locals {
  name_suffix     = terraform.workspace == "default" ? "" : "-${terraform.workspace}"
  bucket_suffix   = var.environment == "production" ? "" : "-${var.environment}"
  tf_state_bucket = "gfw-terraform${local.bucket_suffix}"
  tags            = data.terraform_remote_state.core.outputs.tags
  project         = "gfw-tile-cache"
  container_tag   = substr(var.git_sha, 0, 7)
  tile_cache_url  = "https://${var.tile_cache_url}"
  data_lake_bucket_name = var.data_lake_bucket_name == "" ? data.terraform_remote_state.core.outputs.data-lake_bucket : var.data_lake_bucket_name
}

# Docker file for FastAPI app
module "container_registry" {
  source     = "git::https://github.com/wri/gfw-terraform-modules.git//terraform/modules/container_registry?ref=v0.4.2.4"
  image_name = lower("${local.project}${local.name_suffix}")
  root_dir   = "../${path.root}"
  tag        = local.container_tag
}

module "orchestration" {
  source                       = "git::https://github.com/wri/gfw-terraform-modules.git//terraform/modules/fargate_autoscaling?ref=v0.4.2.4"
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
  task_role_policies           = [
    module.lambda_raster_tiler.lambda_invoke_policy_arn,
    module.storage.s3_write_tiles_arn,
    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
  ]
  task_execution_role_policies = [
    data.terraform_remote_state.core.outputs.secrets_postgresql-reader_policy_arn,
    data.terraform_remote_state.core.outputs.secrets_planet_api_key_policy_arn,
    data.terraform_remote_state.core.outputs.secrets_read-gfw-api-token_policy_arn,
    aws_iam_policy.read_new_relic_secret.arn
  ]
  container_definition         = data.template_file.container_definition.rendered
}

module "content_delivery_network" {
  source              = "./modules/content_delivery_network"
  bucket_domain_name  = module.storage.tiles_bucket_domain_name
  certificate_arn     = data.terraform_remote_state.core.outputs.acm_certificate
  environment         = var.environment
  name_suffix         = local.name_suffix
  project             = local.project
  tags                = local.tags
  website_endpoint    = module.storage.tiles_bucket_website_endpoint
  lambda_edge_runtime = var.lambda_edge_runtime
  tile_cache_app_url  = module.orchestration.lb_dns_name
  log_retention       = var.log_retention
  tile_cache_url      = var.tile_cache_url
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

module "lambda_raster_tiler" {
  source      = "./modules/lambda_raster_tiler"
  environment = var.environment
  lambda_layers = [
    data.terraform_remote_state.lambda_layers.outputs.py310_numpy_1264_arn,
    data.terraform_remote_state.lambda_layers.outputs.py310_pillow_950_arn,
    data.terraform_remote_state.lambda_layers.outputs.py310_rasterio_no_numpy_arn,
    data.terraform_remote_state.lambda_layers.outputs.py310_mercantile_121_arn
  ]
  lambda_runtime = var.lambda_runtime
  log_level  = var.log_level
  project    = local.project
  source_dir = "${path.root}/../lambdas/raster_tiler"
  tags       = local.tags
  data_lake_bucket_name = local.data_lake_bucket_name
  tile_cache_url = local.tile_cache_url
}

resource "aws_iam_policy" "read_new_relic_secret" {
  name = substr("${local.project}-read_new-relic_secret${local.name_suffix}", 0, 64)
  policy = data.aws_iam_policy_document.read_new_relic_lic.json
}