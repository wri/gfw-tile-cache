locals {
  module_name = "tile_cache"
}

data "archive_file" "redirect_latest_tile_cache" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_functions/redirect_latest_tile_cache/src"
  output_path = "${path.module}/lambda_functions/redirect_latest_tile_cache.zip"
}

data "archive_file" "reset_response_header_caching" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_functions/reset_response_header_caching/src"
  output_path = "${path.module}/lambda_functions/reset_response_header_caching.zip"
}

resource "aws_cloudfront_origin_access_identity" "tiles" {}

resource "aws_cloudfront_distribution" "tiles" {

  aliases = var.environment == "production" ? ["tiles.globalforestwatch.org"] : null

  enabled         = true
  http_version    = "http2"
  is_ipv6_enabled = true
  comment         = "tiles.globalforestwatch.org"
  //  default_root_object = "index.html"

  price_class = "PriceClass_All"

  origin {
    domain_name = var.website_endpoint //"gfw-tiles.s3-website-us-east-1.amazonaws.com"
    origin_id   = "wdpa_protected_areas-latest"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_keepalive_timeout = 5
      origin_protocol_policy   = "http-only"
      origin_read_timeout      = 30
      origin_ssl_protocols = [
        "TLSv1",
        "TLSv1.1",
        "TLSv1.2",
      ]
    }
  }
  origin {
    domain_name = "wri-tiles.s3-website-us-east-1.amazonaws.com" // not managed by terraform b/c other account
    origin_id   = "wri-tiles"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_keepalive_timeout = 5
      origin_protocol_policy   = "http-only"
      origin_read_timeout      = 30
      origin_ssl_protocols = [
        "TLSv1",
        "TLSv1.1",
        "TLSv1.2",
      ]
    }
  }
  origin {
    domain_name = var.tile_cache_app_url #"ec2-54-237-221-136.compute-1.amazonaws.com" // not managed by terraform b/c other account
    origin_id   = "fire-tiles"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_keepalive_timeout = 5
      origin_protocol_policy   = "http-only"
      origin_read_timeout      = 30
      origin_ssl_protocols = [
        "TLSv1",
        "TLSv1.1",
        "TLSv1.2",
      ]
    }
  }


  origin {
    domain_name = var.bucket_domain_name // "gfw-tiles.s3.amazonaws.com"
    origin_id   = "S3-gfw-tiles"
    s3_origin_config { origin_access_identity = aws_cloudfront_origin_access_identity.tiles.cloudfront_access_identity_path}
    custom_header {
      name  = "X-Env"
      value = var.environment
    }
  }

  default_cache_behavior {
    allowed_methods  = ["HEAD", "GET"]
    cached_methods   = ["HEAD", "GET"]
    target_origin_id = "S3-gfw-tiles"

    compress = true


    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000

  }

  ordered_cache_behavior {
    allowed_methods = [
      "GET",
      "HEAD",
    ]
    cached_methods = [
      "GET",
      "HEAD",
    ]
    compress               = false
    default_ttl            = 86400
    max_ttl                = 86400
    min_ttl                = 0
    path_pattern           = "glad_prod/*"
    smooth_streaming       = false
    target_origin_id       = "wri-tiles"
    trusted_signers        = []
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      headers                 = []
      query_string            = false
      query_string_cache_keys = []

      cookies {
        forward           = "none"
        whitelisted_names = []
      }
    }
  }

  ordered_cache_behavior {
    allowed_methods = [
      "GET",
      "HEAD",
    ]
    cached_methods = [
      "GET",
      "HEAD",
    ]
    compress               = false
    default_ttl            = 86400
    max_ttl                = 86400
    min_ttl                = 0
    path_pattern           = "nasa_viirs_fire_alerts/*"
    smooth_streaming       = false
    target_origin_id       = "fire-tiles"
    trusted_signers        = []
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      headers                 = []
      query_string            = false
      query_string_cache_keys = []

      cookies {
        forward           = "none"
        whitelisted_names = []
      }
    }
  }

  ordered_cache_behavior {
    allowed_methods = [
      "GET",
      "HEAD",
    ]
    cached_methods = [
      "GET",
      "HEAD",
    ]
    compress               = false
    default_ttl            = 0
    max_ttl                = 31536000
    min_ttl                = 0
    path_pattern           = "*/latest/*"
    smooth_streaming       = false
    target_origin_id       = "S3-gfw-tiles"
    trusted_signers        = []
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      headers                 = []
      query_string            = false
      query_string_cache_keys = []

      cookies {
        forward           = "none"
        whitelisted_names = []
      }
    }

    lambda_function_association {
      event_type   = "origin-request"
      include_body = false
      lambda_arn   = aws_lambda_function.redirect_latest_tile_cache.qualified_arn
    }
    lambda_function_association {
      event_type   = "viewer-response"
      include_body = false
      lambda_arn   = aws_lambda_function.reset_response_header_caching.qualified_arn
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn            = var.certificate_arn
    cloudfront_default_certificate = var.environment == "production" ? false : true
    minimum_protocol_version       = var.environment == "production" ? "TLSv1.1_2016" : "TLSv1"
    ssl_support_method             = var.environment == "production" ? "sni-only" : null
  }


  tags = var.tags

}

resource "aws_lambda_function" "redirect_latest_tile_cache" {
  # TODO: need to give function the correct name
  # Function was imported from core module and we need first to detach it from cloud front, wait until all replicas are deleted and then rename it

  function_name = "core-tile_cache-redirect_latest_tile_cache" # "${var.project}-${local.module_name}-redirect_latest_tile_cache"
  //  function_name    = "redirect_latest_tile_cache"
  filename         = data.archive_file.redirect_latest_tile_cache.output_path
  source_code_hash = data.archive_file.redirect_latest_tile_cache.output_base64sha256
  role             = aws_iam_role.lambda_edge_cloudfront.arn
  runtime          = "nodejs10.x"
  handler          = "lambda_function.handler"
  memory_size      = 128
  timeout          = 3
  publish          = true
  tags             = var.tags
}

resource "aws_lambda_function" "reset_response_header_caching" {
  # TODO: need to give function the correct name
  # Function was imported from core module and we need first to detach it from cloud front, wait until all replicas are deleted and then rename it

  function_name = "core-tile_cache-reset_response_header_caching" # "${var.project}-${local.module_name}-reset_response_header_caching"
  //  function_name    = "reset_response_header_caching"
  filename         = data.archive_file.reset_response_header_caching.output_path
  source_code_hash = data.archive_file.reset_response_header_caching.output_base64sha256
  role             = aws_iam_role.lambda_edge_cloudfront.arn
  runtime          = "nodejs10.x"
  handler          = "lambda_function.handler"
  memory_size      = 128
  timeout          = 1
  publish          = true
  tags             = var.tags

}



#
# Lambda@Edge IAM resources
#

data "aws_iam_policy_document" "lambda_edge_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com",
        "edgelambda.amazonaws.com"
      ]
    }

    actions = ["sts:AssumeRole"]
  }
}


resource "aws_iam_role" "lambda_edge_cloudfront" {
  name               = "${var.project}-tile_cache-lambda_edge_cloudfront"
  assume_role_policy = data.aws_iam_policy_document.lambda_edge_assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_edge_basic_exec" {
  role       = aws_iam_role.lambda_edge_cloudfront.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "s3_read_only" {
  role       = aws_iam_role.lambda_edge_cloudfront.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}