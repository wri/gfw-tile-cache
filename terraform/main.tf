# Require TF version to be same as or greater than 0.12.13
terraform {
  required_version = ">=0.12.19"
  backend "s3" {
    region  = "us-east-1"
    key     = "wri__gfw_fire-vector-tiles.tfstate"
    encrypt = true
  }
}

# Download any stable version in AWS provider of 2.36.0 or higher in 2.36 train
provider "aws" {
  region  = "us-east-1"
  version = "~> 2.49.0"
}

module "container_registry" {
  source     = "git::https://github.com/wri/gfw-terraform-modules.git//modules/container_registry?ref=v0.0.6"
  image_name = lower("${local.project}${local.name_suffix}")
  root_dir   = "../${path.root}"
}






