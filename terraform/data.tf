# import core state
data "terraform_remote_state" "core" {
  backend = "s3"
  config = {
    bucket = local.tf_state_bucket
    region = "us-east-1"
    key    = "core.tfstate"
  }
}


data "terraform_remote_state" "lambda_layers" {
  backend = "s3"
  config = {
    bucket = local.tf_state_bucket
    region = "us-east-1"
    key    = "lambda-layers.tfstate"
  }
}


data "template_file" "container_definition" {
  template = file("${path.root}/templates/container_definition.json.tmpl")
  vars = {
    image = "${module.container_registry.repository_url}:${local.container_tag}"

    container_name = var.container_name
    container_port = var.container_port

    log_group = aws_cloudwatch_log_group.default.name

    reader_secret_arn        = data.terraform_remote_state.core.outputs.secrets_postgresql-reader_arn
    planet_secret_arn        = data.terraform_remote_state.core.outputs.secrets_planet_api_key_arn
    token_secret_arn         = data.terraform_remote_state.core.outputs.secrets_read-gfw-api-token_arn
    log_level                = var.log_level
    project                  = local.project
    environment              = var.environment
    aws_region               = var.region
    tile_cache_url           = local.tile_cache_url
    raster_tiler_lambda_name = module.lambda_raster_tiler.lambda_name
    tiles_bucket_name        = module.storage.tiles_bucket_name
    new_relic_license_key_arn = var.new_relic_license_key_arn
  }
}

data "aws_iam_policy_document" "read_new_relic_lic" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [var.new_relic_license_key_arn]
    effect    = "Allow"
  }
}