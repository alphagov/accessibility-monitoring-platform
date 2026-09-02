resource "aws_db_subnet_group" "main" {
  name       = "${local.app_name}-db-subnets"
  subnet_ids = module.vpc.database_subnets
}

resource "aws_db_instance" "postgres" {
  identifier = "${local.app_name}-postgres"

  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t4g.small"

  allocated_storage = 20
  db_name           = "accessibility_monitoring_app"
  username          = "django"

  multi_az = false

  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  publicly_accessible = false
  skip_final_snapshot = true

  backup_retention_period = 7
}

output "rds_secret_arn" {
  value     = aws_db_instance.postgres.master_user_secret[0].secret_arn
  sensitive = true
}