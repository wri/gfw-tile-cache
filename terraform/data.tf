data "aws_ssm_parameter" "core_contract" {
  name = "/infra/${var.environment}/gfw-aws-core-infra/contract"
}

data "aws_ssm_parameter" "lambda_layers_contract" {
  name = "/infra/${var.environment}/gfw-lambda-layers/contract"
}

locals {
  core          = jsondecode(data.aws_ssm_parameter.core_contract.value)
  lambda_layers = jsondecode(data.aws_ssm_parameter.lambda_layers_contract.value)
}

data "template_file" "container_definition" {
  template = file("${path.root}/templates/container_definition.json.tmpl")
  vars = {
    image = "${module.container_registry.repository_url}:${local.container_tag}"

    container_name = var.container_name
    container_port = var.container_port

    log_group = aws_cloudwatch_log_group.default.name

    reader_secret_arn         = local.core.postgresql_reader_secret_arn
    planet_secret_arn         = local.core.planet_secret_arn
    token_secret_arn          = local.core.gfw_data_api_token_arn
    log_level                 = var.log_level
    project                   = local.project
    environment               = var.environment
    aws_region                = var.region
    tile_cache_url            = local.tile_cache_url
    raster_tiler_lambda_name  = module.lambda_raster_tiler.lambda_name
    tiles_bucket_name         = module.storage.tiles_bucket_name
    new_relic_license_key_arn = data.aws_secretsmanager_secret.newrelic_license.arn
    data_lake_bucket_name     = local.data_lake_bucket_name
  }
}

data "aws_secretsmanager_secret" "newrelic_license" {
  name = var.newrelic_license_key_secret
}

data "aws_iam_policy_document" "read_new_relic_lic" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [data.aws_secretsmanager_secret.newrelic_license.arn]
    effect    = "Allow"
  }
}
