terraform {
  required_version = ">= 0.13, < 0.14"
}

provider "aws" {
  region = "us-east-1"
  skip_credentials_validation = true
  skip_requesting_account_id = true
  skip_metadata_api_check = true
  s3_force_path_style = true
  endpoints {
    s3 = "http://localstack:4566"
    iam = "http://localstack:4566"
    stepfunctions = "http://localstack:4566"
    lambda = "http://localstack:4566"
    cloudwatch = "http://localstack:4566"
    cloudwatchlogs = "http://localstack:4566"
    sts = "http://localstack:4566"
    cloudwatchevents = "http://localstack:4566"
    secretsmanager = "http://localstack:4566"  # pragma: allowlist secret
  }
}

locals {
  lambda_runtime_sn = replace(replace(var.lambda_runtime, ".", ""), "thon", "")
  mercantile_layer_filename = "${var.lambda_runtime}-${var.mercantile_name_version}.zip"
  pillow_layer_filename = "${var.lambda_runtime}-${var.pillow_name_version}.zip"
  rasterio_layer_filename = "${var.lambda_runtime}-${var.rasterio_name_version}.zip"
}

resource "aws_s3_bucket" "data_lake_test" {
  bucket = "gfw-data-lake-test"
  acl    = "private"
  force_destroy = true
}

resource "aws_s3_bucket" "pipelines_test" {
  bucket = "gfw-pipelines-test"
  acl    = "private"
  force_destroy = true
}

resource "aws_s3_bucket" "tiles_test" {
  bucket = "gfw-tiles-test"
  acl    = "private"
  force_destroy = true
}

resource "aws_s3_bucket_object" "rasterio_layer" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/${local.rasterio_layer_filename}"
  source = "../fixtures/${local.rasterio_layer_filename}"
  etag   = filemd5("../fixtures/${local.rasterio_layer_filename}")
}

resource "aws_lambda_layer_version" "rasterio_layer" {
  layer_name          = substr("${local.lambda_runtime_sn}_${replace(var.rasterio_name_version, ".", "")}", 0, 64)
  s3_bucket           = aws_s3_bucket_object.rasterio_layer.bucket
  s3_key              = aws_s3_bucket_object.rasterio_layer.key
  compatible_runtimes = [var.lambda_runtime]
  source_code_hash    = filebase64sha256(
    "../fixtures/${local.rasterio_layer_filename}"
  )
}

resource "aws_s3_bucket_object" "pillow_layer" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/${local.pillow_layer_filename}"
  source = "../fixtures/${local.pillow_layer_filename}"
  etag   = filemd5("../fixtures/${local.pillow_layer_filename}")
}

resource "aws_lambda_layer_version" "pillow_layer" {
  layer_name          = substr("${local.lambda_runtime_sn}_${replace(var.pillow_name_version, ".", "")}", 0, 64)
  s3_bucket           = aws_s3_bucket_object.pillow_layer.bucket
  s3_key              = aws_s3_bucket_object.pillow_layer.key
  compatible_runtimes = [var.lambda_runtime]
  source_code_hash    = filebase64sha256(
    "../fixtures/${local.pillow_layer_filename}"
  )
}

resource "aws_s3_bucket_object" "mercantile_layer" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/${local.mercantile_layer_filename}"
  source = "../fixtures/${local.mercantile_layer_filename}"
  etag   = filemd5("../fixtures/${local.mercantile_layer_filename}")
}

resource "aws_lambda_layer_version" "mercantile_layer" {
  layer_name          = substr("${local.lambda_runtime_sn}_${replace(var.mercantile_name_version, ".", "")}", 0, 64)
  s3_bucket           = aws_s3_bucket_object.mercantile_layer.bucket
  s3_key              = aws_s3_bucket_object.mercantile_layer.key
  compatible_runtimes = [var.lambda_runtime]
  source_code_hash    = filebase64sha256(
    "../fixtures/${local.mercantile_layer_filename}"
  )
}

module "lambda_raster_tiler" {
  source      = "../../terraform/modules/lambda_raster_tiler"
  environment = "test"
  lambda_layers = [
    aws_lambda_layer_version.pillow_layer.arn,
    aws_lambda_layer_version.rasterio_layer.arn,
    aws_lambda_layer_version.mercantile_layer.arn
  ]
  lambda_runtime = var.lambda_runtime
  log_level  = "debug"
  project    = "test_project"
  source_dir = "../../lambdas/raster_tiler"
  tags       = {}
  data_lake_bucket_name = "gfw-data-lake-test"
  tile_cache_url = "http://localstack:4566"
}