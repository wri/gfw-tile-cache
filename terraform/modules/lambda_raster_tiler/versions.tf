terraform {
  required_providers {
    archive = {
      source = "hashicorp/archive"
    }
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5, < 6"
    }
  }
  required_version = ">= 0.13, < 0.14"
}