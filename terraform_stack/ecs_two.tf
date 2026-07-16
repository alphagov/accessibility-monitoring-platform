resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.app_name}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "${local.app_name}-worker"
      image = "${aws_ecr_repository.worker.repository_url}:${var.worker_image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = 8001
          hostPort      = 8001
        }
      ]

      environment = [
        { name = "ALLOWED_HOSTS", value = "${var.app_two_domain_name} ${aws_lb.app.dns_name}"},
        { name = "DB_HOST", value = aws_db_instance.postgres.address },
        { name = "DB_NAME", value = aws_db_instance.postgres.db_name },
        { name = "DB_USER", value = aws_db_instance.postgres.username },
        { name = "AWS_REGION", value = "eu-west-2" },
        { name = "TERRAFORM", value = "TRUE" },
        { name = "BUCKET_NAME", value = aws_s3_bucket.app_files.bucket },
        { name = "AWS_S3_REGION_NAME", value = "eu-west-2" }
      ]

      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = aws_db_instance.postgres.master_user_secret[0].secret_arn
        },
        {
          name      = "SECRET_KEY"
          valueFrom = aws_secretsmanager_secret.django_secret_key.arn
        },
        {
          name      = "NOTIFY_API_KEY"
          valueFrom = data.aws_secretsmanager_secret.notify_api_key.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = "eu-west-2"
          awslogs-stream-prefix = "worker"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "worker" {
  name             = "${local.app_name}-worker"
  cluster          = aws_ecs_cluster.main.id
  task_definition  = aws_ecs_task_definition.worker.arn
  desired_count    = 1
  launch_type      = "FARGATE"
  platform_version = "1.4.0"
  force_new_deployment = true
  enable_execute_command = true
  health_check_grace_period_seconds = 300


  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.worker.arn
    container_name   = "${local.app_name}-worker"
    container_port   = 8001
  }

  depends_on = [aws_lb_listener.https]
}