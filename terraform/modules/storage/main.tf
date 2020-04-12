
resource "aws_s3_bucket" "tiles" {
  bucket = "gfw-tiles${var.bucket_suffix}"
  acl    = "private"
  tags   = var.tags

  cors_rule {
    allowed_headers = [
      "Authorization",
    ]
    allowed_methods = [
      "GET",
    ]
    allowed_origins = [
      "*",
    ]
    expose_headers  = []
    max_age_seconds = 3000
  }

}

resource "aws_s3_bucket" "tiles-test" {
  bucket = "gfw-tiles-test"
  acl    = "private"
  tags   = var.tags
  count  = var.environment == "dev" ? 1 : 0
}

resource "aws_s3_bucket_policy" "tiles" {
  bucket = aws_s3_bucket.tiles.id
  policy = module.tiles_policy.result_document

}


module "tiles_policy" {
  source = "git::https://github.com/cloudposse/terraform-aws-iam-policy-document-aggregator.git?ref=0.2.0"
  source_documents = [
    //    data.template_file.tiles_bucket_policy_public.rendered,
    data.template_file.tiles_bucket_policy_cloudfront.rendered,
    data.template_file.tiles_bucket_policy_lambda.rendered
  ]
}


//data "template_file" "tiles_bucket_policy_public" {
//  template = file("${path.root}/policies/bucket_policy_public_read.json.tpl")
//  vars = {
//    bucket_arn = aws_s3_bucket.tiles.arn
//  }
//}

data "template_file" "tiles_bucket_policy_cloudfront" {
  template = file("${path.root}/policies/bucket_policy_role_read.json.tpl")
  vars = {
    bucket_arn       = aws_s3_bucket.tiles.arn
    aws_resource_arn = var.cloudfront_access_identity_iam_arn
  }
}


data "template_file" "tiles_bucket_policy_lambda" {
  template = file("${path.root}/policies/bucket_policy_role_read.json.tpl")
  vars = {
    bucket_arn       = aws_s3_bucket.tiles.arn
    aws_resource_arn = var.lambda_edge_cloudfront_arn
  }
}

data "template_file" "s3_write_tiles" {
  template = file("${path.root}/policies/iam_policy_s3_write.json.tpl")
  vars = {
    bucket_arn = aws_s3_bucket.tiles.arn
  }
}

resource "aws_iam_policy" "s3_write_tiles" {
  name   = "${var.project}-s3_write_tiles"
  policy = data.template_file.s3_write_tiles.rendered

}