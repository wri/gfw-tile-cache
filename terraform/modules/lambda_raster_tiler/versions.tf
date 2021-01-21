terraform {
  required_providers {
    archive = {
      source = "hashicorp/archive"
    }
    aws = {
      source  = "hashicorp/aws"
      version = ">=3, <4"
    }
  }
  required_version = ">= 0.13"
}
