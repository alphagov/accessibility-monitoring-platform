resource "aws_ecr_repository" "app" {
  name = "${local.app_name}-web"
}

resource "aws_ecr_repository" "viewer" {
  name = "${local.app_name}-viewer"
}