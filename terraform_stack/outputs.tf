output "alb_dns_name" {
  value = aws_lb.app.dns_name
}

output "app_url" {
  value = aws_acm_certificate.app.domain_name
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "web_ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "worker_ecr_repository_url" {
  value = aws_ecr_repository.worker.repository_url
}

output "target_group_arn" {
  value = aws_lb_target_group.app.arn
}

output "s3_bucket_name" {
  value = aws_s3_bucket.app_files.bucket
}

output "app_name" {
  value = local.app_name
}

output "ecs_one_name" {
  value = aws_ecs_service.app.name
}