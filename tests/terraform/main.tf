terraform {
  required_version = ">=0.13"
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
    secretsmanager = "http://localstack:4566"
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

resource "aws_s3_bucket_object" "py38_rasterio_118" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/python3.8-rasterio_1.1.8.zip"
  source = "../fixtures/python3.8-rasterio_1.1.8.zip"
  etag   = filemd5("../fixtures/python3.8-rasterio_1.1.8.zip")
}

resource "aws_lambda_layer_version" "py38_rasterio_118" {
  layer_name          = substr("py38_rasterio_118", 0, 64)
  s3_bucket           = aws_s3_bucket_object.py38_rasterio_118.bucket
  s3_key              = aws_s3_bucket_object.py38_rasterio_118.key
  compatible_runtimes = ["python3.8"]
  source_code_hash    = filebase64sha256("../fixtures/python3.8-rasterio_1.1.8.zip")
}

resource "aws_s3_bucket_object" "py38_pillow_801" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/python3.8-pillow_8.0.1.zip"
  source = "../fixtures/python3.8-pillow_8.0.1.zip"
  etag   = filemd5("../fixtures/python3.8-pillow_8.0.1.zip")
}

resource "aws_lambda_layer_version" "py38_pillow_801" {
  layer_name          = substr("py38_pillow_801", 0, 64)
  s3_bucket           = aws_s3_bucket_object.py38_pillow_801.bucket
  s3_key              = aws_s3_bucket_object.py38_pillow_801.key
  compatible_runtimes = ["python3.8"]
  source_code_hash    = filebase64sha256("../fixtures/python3.8-pillow_8.0.1.zip")
}

module "lambda_raster_tiler" {
  source      = "../../terraform/modules/lambda_raster_tiler"
  environment = "test"
  lambda_layers = [aws_lambda_layer_version.py38_pillow_801.arn, aws_lambda_layer_version.py38_rasterio_118.arn]
  log_level  = "debug"
  project    = "test_project"
  source_dir = "../../lambdas/raster_tiler"
  tags       = {}
  data_lake_bucket_name = "gfw-data-lake-test"
}