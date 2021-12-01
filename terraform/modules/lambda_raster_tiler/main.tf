######################
# Lambda Function
######################


data "archive_file" "default" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.module}/archive/app.zip"
}


resource "aws_lambda_function" "default" {
  # Function was imported from core module and we need first to detach it
  # from cloud front, wait until all replicas are deleted and then rename it

  function_name    = "${var.project}-lambda-tiler"
  filename         = data.archive_file.default.output_path
  source_code_hash = data.archive_file.default.output_base64sha256
  role             = aws_iam_role.default.arn
  layers           = var.lambda_layers
  runtime          = "python3.8"
  handler          = "lambda_function.handler"
  memory_size      = 128
  timeout          = 30
  publish          = true
  tags             = var.tags
  environment {
    variables = {
      DATA_LAKE_BUCKET    = var.data_lake_bucket_name
      LOG_LEVEL = var.log_level
      ENV       = var.environment
      TILE_CACHE_URL = var.tile_cache_url
    }
  }
}


##########################
# Logging
##########################

resource "aws_cloudwatch_log_group" "default" {
  name              = "/aws/lambda/${aws_lambda_function.default.function_name}"
  retention_in_days = var.log_retention
}


############################
## IAM resources
############################

data "aws_iam_policy_document" "default" {
  statement {
    effect = "Allow"

    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com"
      ]
    }

    actions = [
    "sts:AssumeRole"]
  }
}


resource "aws_iam_role" "default" {
  name               = "${var.project}_role"
  assume_role_policy = data.aws_iam_policy_document.default.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic_exec" {
  role       = aws_iam_role.default.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "read_s3" {
  role       = aws_iam_role.default.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}



data "template_file" "iam_lambda_invoke" {
  template = file("${path.module}/templates/lambda_invoke_policy.json.tmpl")
  vars = {
    resource = aws_lambda_function.default.arn
  }
}

resource "aws_iam_policy" "lambda_invoke" {
  name = "${aws_lambda_function.default.function_name}-invoke"
  //  policy = data.template_file.iam_lambda_invoke.rendered
  policy = data.template_file.iam_lambda_invoke.rendered
}