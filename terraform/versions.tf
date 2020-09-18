terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      region  = "us-east-1"
      version = "~> 3.0"
    }
    template = {
      source = "hashicorp/template"
    }
  }
  required_version = "~> 0.13"
}
