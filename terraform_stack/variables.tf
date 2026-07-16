variable "domain_name" {
  type        = string
  description = "Root domain name in Route 53, e.g. example.com"
}

variable "app_domain_name" {
  type        = string
  description = "App domain name, e.g. app.example.com"
}

variable "app_two_domain_name" {
  type        = string
  description = "App domain name for second service, e.g. app.example.com"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "image_tag" {
  type        = string
  description = "Docker image tag to deploy"
  default     = "latest"
}

variable "worker_image_tag" {
  type        = string
  description = "Worker Docker image tag to deploy"
  default     = "latest"
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
}

variable "app_name" {
  type    = string
  default = "default-app-name"
}
