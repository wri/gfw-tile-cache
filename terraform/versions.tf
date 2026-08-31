terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5, < 6"
      region  = "us-east-1"
    }
    template = {
      source = "hashicorp/template"
    }
  }
  required_version = "= 0.13.3"
}