provider "aws" {
  region = var.aws_region
}

locals {
  app_name = "amp-app-${var.environment}"
}

