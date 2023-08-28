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
  key    = "lambda_layers/${var.lambda_runtime}-rasterio_1.3.8.zip"
  source = "../fixtures/${var.lambda_runtime}-rasterio_1.3.8.zip"
  etag   = filemd5("../fixtures/${var.lambda_runtime}-rasterio_1.3.8.zip")
}

resource "aws_lambda_layer_version" "rasterio_layer" {
  layer_name          = substr("${var.lambda_runtime_sn}_rasterio_138", 0, 64)
  s3_bucket           = aws_s3_bucket_object.rasterio_layer.bucket
  s3_key              = aws_s3_bucket_object.rasterio_layer.key
  compatible_runtimes = [var.lambda_runtime]
  source_code_hash    = filebase64sha256("../fixtures/python3.10-rasterio_1.3.8.zip")
}

resource "aws_s3_bucket_object" "pillow_layer" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/${var.lambda_runtime}-pillow_9.5.0.zip"
  source = "../fixtures/${var.lambda_runtime}-pillow_9.5.0.zip"
  etag   = filemd5("../fixtures/${var.lambda_runtime}-pillow_9.5.0.zip")
}

resource "aws_lambda_layer_version" "pillow_layer" {
  layer_name          = substr("${var.lambda_runtime_sn}_pillow_950", 0, 64)
  s3_bucket           = aws_s3_bucket_object.pillow_layer.bucket
  s3_key              = aws_s3_bucket_object.pillow_layer.key
  compatible_runtimes = [var.lambda_runtime]
  source_code_hash    = filebase64sha256("../fixtures/${var.lambda_runtime}-pillow_9.5.0.zip")
}

resource "aws_s3_bucket_object" "mercantile_layer" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/${var.lambda_runtime}-mercantile_1.2.1.zip"
  source = "../fixtures/${var.lambda_runtime}-mercantile_1.2.1.zip"
  etag   = filemd5("../fixtures/${var.lambda_runtime}-mercantile_1.2.1.zip")
}

resource "aws_lambda_layer_version" "mercantile_layer" {
  layer_name          = substr("${var.lambda_runtime_sn}_mercantile_121", 0, 64)
  s3_bucket           = aws_s3_bucket_object.mercantile_layer.bucket
  s3_key              = aws_s3_bucket_object.mercantile_layer.key
  compatible_runtimes = [var.lambda_runtime]
  source_code_hash    = filebase64sha256("../fixtures/${var.lambda_runtime}-mercantile_1.2.1.zip")
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