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

resource "aws_s3_bucket_object" "py310_rasterio_134" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/python3.8-rasterio_1.1.8.zip"
  source = "../fixtures/python3.10-rasterio_1.3.4.zip"
  etag   = filemd5("../fixtures/python3.10-rasterio_1.3.4.zip")
}

resource "aws_lambda_layer_version" "py310_rasterio_134" {
  layer_name          = substr("py310_rasterio_134", 0, 64)
  s3_bucket           = aws_s3_bucket_object.py310_rasterio_134.bucket
  s3_key              = aws_s3_bucket_object.py310_rasterio_134.key
  compatible_runtimes = ["python3.10"]
  source_code_hash    = filebase64sha256("../fixtures/python3.10-rasterio_1.3.4.zip")
}

resource "aws_s3_bucket_object" "py310_pillow_950" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/python3.10-pillow_9.5.0.zip"
  source = "../fixtures/python3.10-pillow_9.5.0.zip"
  etag   = filemd5("../fixtures/python3.10-pillow_9.5.0.zip")
}

resource "aws_lambda_layer_version" "py310_pillow_950" {
  layer_name          = substr("py310_pillow_950", 0, 64)
  s3_bucket           = aws_s3_bucket_object.py310_pillow_950.bucket
  s3_key              = aws_s3_bucket_object.py310_pillow_950.key
  compatible_runtimes = ["python3.10"]
  source_code_hash    = filebase64sha256("../fixtures/python3.10-pillow_9.5.0.zip")
}


resource "aws_s3_bucket_object" "py310_mercantile_121" {
  bucket = aws_s3_bucket.pipelines_test.id
  key    = "lambda_layers/python3.10-mercantile_1.2.1.zip"
  source = "../fixtures/python3.10-mercantile_1.2.1.zip"
  etag   = filemd5("../fixtures/python3.10-mercantile_1.2.1.zip")
}

resource "aws_lambda_layer_version" "py310_mercantile_121" {
  layer_name          = substr("py310_mercantile_121", 0, 64)
  s3_bucket           = aws_s3_bucket_object.py310_mercantile_121.bucket
  s3_key              = aws_s3_bucket_object.py310_mercantile_121.key
  compatible_runtimes = ["python3.10"]
  source_code_hash    = filebase64sha256("../fixtures/python3.10-mercantile_1.2.1.zip")
}

module "lambda_raster_tiler" {
  source      = "../../terraform/modules/lambda_raster_tiler"
  environment = "test"
  lambda_layers = [
    aws_lambda_layer_version.py310_pillow_950.arn,
    aws_lambda_layer_version.py310_rasterio_134.arn,
    aws_lambda_layer_version.py310_mercantile_121.arn]
  log_level  = "debug"
  project    = "test_project"
  source_dir = "../../lambdas/raster_tiler"
  tags       = {}
  data_lake_bucket_name = "gfw-data-lake-test"
  tile_cache_url = "http://localstack:4566"
}