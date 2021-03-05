############################
## Cloud Front Distribution
############################

locals {
  methods = ["GET", "HEAD", "OPTIONS"]
  headers = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]
  suffix  = var.environment == "production" ? "" : "-${var.environment}"
}

resource "aws_cloudfront_origin_access_identity" "tiles" {}

resource "aws_cloudfront_distribution" "tiles" {

  aliases = [var.tile_cache_url]

  enabled         = true
  http_version    = "http2"
  is_ipv6_enabled = true
  comment         = var.tile_cache_url
  price_class     = "PriceClass_All"


  // not managed by terraform b/c other account
  // should be removed eventually once all tiles are migrated into new account
  origin {
    domain_name = "wri-tiles.s3-website-us-east-1.amazonaws.com"
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


  // not managed by terraform b/c other account
  // used for tiles generated in GEE
  origin {
    domain_name = "storage.googleapis.com"
    origin_id   = "google-tiles"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_keepalive_timeout = 5
      origin_protocol_policy   = "https-only"
      origin_read_timeout      = 30
      origin_ssl_protocols = [
        "TLSv1",
        "TLSv1.1",
        "TLSv1.2",
      ]
    }
  }

  // Tile Cache App hosted on AWS Fargate with Load Balancer
  origin {
    domain_name = var.tile_cache_app_url
    origin_id   = "dynamic"

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

  # GFW Tile Cache S3 Bucket
  origin {
    domain_name = var.bucket_domain_name
    origin_id   = "static"
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.tiles.cloudfront_access_identity_path
    }

    # Tell Lambda@Edge function what environment we are in
    custom_header {
      name  = "X-Env"
      value = var.environment
    }

    # Tell Lambda@Edge were to redirect 404 responses
    custom_header {
      name  = "X-tile-cache-app"
      value = var.tile_cache_app_url
    }
  }

  # send all uncached URIs to tile cache app
  default_cache_behavior {
    allowed_methods        = local.methods
    cached_methods         = local.methods
    compress               = true
    default_ttl            = 86400 # 24h
    max_ttl                = 86400 # 24h
    min_ttl                = 0
    smooth_streaming       = false
    target_origin_id       = "dynamic"
    trusted_signers        = []
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      headers                 = local.headers
      query_string            = true
      query_string_cache_keys = []

      cookies {
        forward           = "none"
        whitelisted_names = []
      }
    }
  }


  # Latest default layers need to be rerouted and cache headers need to be rewritten
  # This cache bahavior sends the requests to a lambda@edge function which looks up the latest version
  # and then returns a 307 with the correct version number.
  # Responses are cached for 6 hours
  ordered_cache_behavior {
    allowed_methods        = local.methods
    cached_methods         = local.methods
    compress               = false
    default_ttl            = 21600 # 6h
    max_ttl                = 21600 # 6h
    min_ttl                = 0
    path_pattern           = "*/latest/*"
    smooth_streaming       = false
    target_origin_id       = "static"
    trusted_signers        = []
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      headers                 = local.headers
      query_string            = false
      query_string_cache_keys = []

      cookies {
        forward           = "none"
        whitelisted_names = []
      }
    }

    lambda_function_association {
      event_type   = "viewer-request"
      include_body = false
      lambda_arn   = aws_lambda_function.redirect_latest_tile_cache.qualified_arn
    }

  }


  # Legacy behavior
  # Should be deprecated, once GLAD alerts run in new GFW account and live in data lake
  #
  # Fetches GLAD tiles from WRI S3 account.
  # Bucket itself is configured to forward 404s to a lambda function
  # which will generate dynamic tiles for zoom level 9 and up.
  # The redirected URL is not cached in cloud front.
  # Static tiles from S3 are cached for 12 hours
  ordered_cache_behavior {
    allowed_methods        = local.methods
    cached_methods         = local.methods
    compress               = false
    default_ttl            = 43200 # 12h
    max_ttl                = 43200 # 12h
    min_ttl                = 0
    path_pattern           = "glad_prod/*"
    smooth_streaming       = false
    target_origin_id       = "wri-tiles"
    trusted_signers        = []
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      headers                 = local.headers
      query_string            = false
      query_string_cache_keys = []

      cookies {
        forward           = "none"
        whitelisted_names = []
      }
    }
  }

  ###################################################
  # Externally managed
  # TCL data are currently generated in GEE and stored in GCS
  # We update the response header to keep the tiles in browser cache for up to a year
  # Cloud front will also cache tile for a year
  ###################################################

  #####################
  # UMD Tree Cover Loss
  #####################
  ordered_cache_behavior {
    allowed_methods        = local.methods
    cached_methods         = local.methods
    compress               = true
    default_ttl            = 31536000 # 1y
    max_ttl                = 31536000 # 1y
    min_ttl                = 0
    path_pattern           = "umd_tree_cover_loss/v1.7/tcd*"
    smooth_streaming       = false
    target_origin_id       = "google-tiles"
    trusted_signers        = []
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      headers                 = local.headers
      query_string            = false
      query_string_cache_keys = []

      cookies {
        forward           = "none"
        whitelisted_names = []
      }
    }

    lambda_function_association {
      event_type   = "origin-response"
      include_body = false
      lambda_arn   = aws_lambda_function.response_header_cache_control.qualified_arn
    }
  }

  #####################
  # WHRC Above ground biomass loss
  #####################
  ordered_cache_behavior {
    allowed_methods        = local.methods
    cached_methods         = local.methods
    compress               = true
    default_ttl            = 31536000 # 1y
    max_ttl                = 31536000 # 1y
    min_ttl                = 0
    path_pattern           = "whrc_aboveground_biomass_loss/v4.1.7*"
    smooth_streaming       = false
    target_origin_id       = "google-tiles"
    trusted_signers        = []
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      headers                 = local.headers
      query_string            = false
      query_string_cache_keys = []

      cookies {
        forward           = "none"
        whitelisted_names = []
      }
    }

    lambda_function_association {
      event_type   = "origin-response"
      include_body = false
      lambda_arn   = aws_lambda_function.response_header_cache_control.qualified_arn
    }
  }

  #####################
  # TSC Tree cover loss drivers
  #####################

  ordered_cache_behavior {
    allowed_methods        = local.methods
    cached_methods         = local.methods
    compress               = true
    default_ttl            = 31536000 # 1y
    max_ttl                = 31536000 # 1y
    min_ttl                = 0
    path_pattern           = "tsc_tree_cover_loss_drivers/v2020/*"
    smooth_streaming       = false
    target_origin_id       = "google-tiles"
    trusted_signers        = []
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      headers                 = local.headers
      query_string            = false
      query_string_cache_keys = []

      cookies {
        forward           = "none"
        whitelisted_names = []
      }
    }

    lambda_function_association {
      event_type   = "origin-response"
      include_body = false
      lambda_arn   = aws_lambda_function.response_header_cache_control.qualified_arn
    }
  }


  # Default static raster tiles are stored on S3
  # They won't change and can stay in cache for a year
  # We will set response headers for selected tile caches in S3 if required
  # If tile is not found on S3, redirect to tile cache app (`dynamic` endpoint).
  # Tile cache app will return dynamically generated tile and upload tile to s3 for future use
  # or raise 404 error if tile does not exist.
  ordered_cache_behavior {
    allowed_methods  = local.methods
    cached_methods   = local.methods
    target_origin_id = "static"
    compress         = true
    path_pattern     = "*/default/*.png"

    forwarded_values {
      query_string = false
      headers      = local.headers
      cookies {
        forward = "none"
      }
    }

    lambda_function_association {
      event_type   = "origin-response"
      include_body = false
      lambda_arn   = aws_lambda_function.redirect_s3_404.qualified_arn
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 31536000 # 1y
    max_ttl                = 31536000 # 1y

  }


  # send all WMTS requests to tile cache app
  ordered_cache_behavior {
    allowed_methods        = local.methods
    cached_methods         = local.methods
    target_origin_id       = "dynamic"
    compress               = true
    path_pattern           = "*/wmts"
    default_ttl            = 86400 # 24h
    max_ttl                = 86400 # 24h
    min_ttl                = 0
    smooth_streaming       = false
    trusted_signers        = []
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      headers                 = local.headers
      query_string            = true
      query_string_cache_keys = []

      cookies {
        forward           = "none"
        whitelisted_names = []
      }
    }
  }

  # Default static vector tiles are stored on S3
  # They won't change and can stay in cache for a year
  # We will set response headers for selected tile caches in S3 if required
  ordered_cache_behavior {
    allowed_methods  = local.methods
    cached_methods   = local.methods
    target_origin_id = "static"
    compress         = true
    path_pattern     = "*/default/*"

    forwarded_values {
      query_string = false
      headers      = local.headers
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 31536000 # 1y
    max_ttl                = 31536000 # 1y

  }

  # send all dynamic URIs to tile cache app
  ordered_cache_behavior {
    allowed_methods        = local.methods
    cached_methods         = local.methods
    target_origin_id       = "dynamic"
    compress               = true
    path_pattern           = "*/dynamic/*"
    default_ttl            = 86400 # 24h
    max_ttl                = 86400 # 24h
    min_ttl                = 0
    smooth_streaming       = false
    trusted_signers        = []
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      headers                 = local.headers
      query_string            = true
      query_string_cache_keys = []

      cookies {
        forward           = "none"
        whitelisted_names = []
      }
    }
  }

  # Non default static tiles are stored on S3.
  # There might be some static raster tile caches which don't have default in their name.
  # We need to cache them somehow. In consequence, dynamic raster tile caches must always have `dynamic` in their name.
  # If tile is not found on S3, redirect to tile cache app (`dynamic` endpoint).
  # Tile cache app will return dynamically generated tile and upload tile to s3 for future use
  # or raise 404 error if tile does not exist.
  ordered_cache_behavior {
    allowed_methods        = local.methods
    cached_methods         = local.methods
    target_origin_id       = "static"
    compress               = true
    path_pattern           = "*.png"
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 31536000 # 1y
    max_ttl                = 31536000 # 1y

    forwarded_values {
      query_string = false
      headers      = local.headers
      cookies {
        forward = "none"
      }
    }

    lambda_function_association {
      event_type   = "origin-response"
      include_body = false
      lambda_arn   = aws_lambda_function.redirect_s3_404.qualified_arn
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn            = var.certificate_arn
    cloudfront_default_certificate = false
    minimum_protocol_version       = "TLSv1.1_2016"
    ssl_support_method             = "sni-only"
  }


  tags = var.tags

}

#########################
## IAM
#########################

data "template_file" "create_cloudfront_invalidation" {
  template = file("${path.root}/templates/iam_policy_create_cloudfront_invalidation.json.tmpl")
  vars = {
    cloudfront_arn = aws_cloudfront_distribution.tiles.arn
  }
}

resource "aws_iam_policy" "create_cloudfront_invalidation" {
  name   = "${var.project}-create_cloudfront_invalidation${var.name_suffix}"
  policy = data.template_file.create_cloudfront_invalidation.rendered

}


#########################
## Lambda@Edge Functions
#########################

data "archive_file" "redirect_latest_tile_cache" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_functions/redirect_latest_tile_cache/src"
  output_path = "${path.module}/lambda_functions/redirect_latest_tile_cache.zip"
}

data "archive_file" "redirect_s3_404" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_functions/redirect_s3_404/src"
  output_path = "${path.module}/lambda_functions/redirect_s3_404.zip"
}

data "archive_file" "response_header_cache_control" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_functions/response_header_cache_control/src"
  output_path = "${path.module}/lambda_functions/response_header_cache_control.zip"
}

resource "aws_lambda_function" "redirect_latest_tile_cache" {
  # Function was imported from core module and we need first to detach it from cloud front, wait until all replicas are deleted and then rename it

  function_name    = "${var.project}-redirect_latest_tile_cache${var.name_suffix}"
  filename         = data.archive_file.redirect_latest_tile_cache.output_path
  source_code_hash = data.archive_file.redirect_latest_tile_cache.output_base64sha256
  role             = aws_iam_role.lambda_edge_cloudfront.arn
  runtime          = "python3.8"
  handler          = "lambda_function.handler"
  memory_size      = 128
  timeout          = 3
  publish          = true
  tags             = var.tags
}

resource "aws_lambda_function" "redirect_s3_404" {

  function_name    = "${var.project}-redirect_s3_404${var.name_suffix}"
  filename         = data.archive_file.redirect_s3_404.output_path
  source_code_hash = data.archive_file.redirect_s3_404.output_base64sha256
  role             = aws_iam_role.lambda_edge_cloudfront.arn
  runtime          = "python3.8"
  handler          = "lambda_function.handler"
  memory_size      = 128
  timeout          = 3
  publish          = true
  tags             = var.tags
}

resource "aws_lambda_function" "response_header_cache_control" {

  function_name    = "${var.project}-response_header_cache_control${var.name_suffix}"
  filename         = data.archive_file.response_header_cache_control.output_path
  source_code_hash = data.archive_file.response_header_cache_control.output_base64sha256
  role             = aws_iam_role.lambda_edge_cloudfront.arn
  runtime          = "python3.8"
  handler          = "lambda_function.handler"
  memory_size      = 128
  timeout          = 3
  publish          = true
  tags             = var.tags
}

############################
## Lambda@Edge IAM resources
############################

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

    actions = [
    "sts:AssumeRole"]
  }
}


resource "aws_iam_role" "lambda_edge_cloudfront" {
  name               = "${var.project}-tile_cache-lambda_edge_cloudfront${var.name_suffix}"
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

##################
## Logging
##################


data "aws_regions" "current" {
  all_regions = true
}


resource "aws_cloudwatch_log_group" "lambda_redirect_latest" {
  count = length(tolist(data.aws_regions.current.names))

  name              = "/aws/lambda/${tolist(data.aws_regions.current.names)[count.index]}.${var.project}-redirect_latest_tile_cache${var.name_suffix}"
  retention_in_days = var.log_retention
}

resource "aws_cloudwatch_log_group" "redirect_s3_404" {
  count = length(tolist(data.aws_regions.current.names))

  name              = "/aws/lambda/${tolist(data.aws_regions.current.names)[count.index]}.${var.project}-redirect_s3_404${var.name_suffix}"
  retention_in_days = var.log_retention
}

resource "aws_cloudwatch_log_group" "response_header_cache_control" {
  count = length(tolist(data.aws_regions.current.names))

  name              = "/aws/lambda/${tolist(data.aws_regions.current.names)[count.index]}.${var.project}-response_header_cache_control${var.name_suffix}"
  retention_in_days = var.log_retention
}
