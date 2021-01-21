output "lambda_arn" {
  value = aws_lambda_function.default.arn
}

output "lambda_name" {
  value = aws_lambda_function.default.function_name
}

output "lambda_invoke_policy_arn" {
  value = aws_iam_policy.lambda_invoke.arn
}