//
//#
//# API Gateway resources
//#
//resource "aws_api_gateway_vpc_link" "default" {
//  name        = "${local.project}-gateway_vpc_link${local.name_suffix}"
//  target_arns = [aws_lb.default.arn]
//}
//
//resource "aws_api_gateway_rest_api" "default" {
//  name = "${local.project}-gateway${local.name_suffix}"
//}
//
//resource "aws_api_gateway_resource" "proxy" {
//  rest_api_id = aws_api_gateway_rest_api.default.id
//  parent_id   = aws_api_gateway_rest_api.default.root_resource_id
//  path_part   = "{proxy+}"
//}
//
//resource "aws_api_gateway_method" "proxy" {
//  rest_api_id   = aws_api_gateway_rest_api.default.id
//  resource_id   = aws_api_gateway_resource.proxy.id
//  http_method   = "ANY"
//  authorization = "NONE"
//}
//
//resource "aws_api_gateway_integration" "nlb" {
//  rest_api_id = aws_api_gateway_rest_api.default.id
//  resource_id = aws_api_gateway_method.proxy.resource_id
//  http_method = aws_api_gateway_method.proxy.http_method
//
//  integration_http_method = "ANY"
//  type                    = "HTTP_PROXY"
//  connection_type         = "VPC_LINK"
//  connection_id           = aws_api_gateway_vpc_link.default.id
//  uri                     = "http://${aws_lb.default.dns_name}"
//}
//
//resource "aws_api_gateway_method" "proxy_root" {
//  rest_api_id   = aws_api_gateway_rest_api.default.id
//  resource_id   = aws_api_gateway_rest_api.default.root_resource_id
//  http_method   = "ANY"
//  authorization = "NONE"
//}
//
//resource "aws_api_gateway_integration" "nlb_root" {
//  rest_api_id = aws_api_gateway_rest_api.default.id
//  resource_id = aws_api_gateway_method.proxy_root.resource_id
//  http_method = aws_api_gateway_method.proxy_root.http_method
//
//  integration_http_method = "ANY"
//  type                    = "HTTP_PROXY"
//  connection_type         = "VPC_LINK"
//  connection_id           = aws_api_gateway_vpc_link.default.id
//  uri                     = "http://${aws_lb.default.dns_name}"
//}
//
//resource "aws_api_gateway_deployment" "default" {
//  depends_on = [
//    aws_api_gateway_integration.nlb,
//    aws_api_gateway_integration.nlb_root,
//  ]
//
//  rest_api_id = aws_api_gateway_rest_api.default.id
//  stage_name  = "default"
//}