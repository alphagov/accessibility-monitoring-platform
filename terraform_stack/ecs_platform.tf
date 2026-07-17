resource "aws_ecs_cluster" "main" {
  name = "${local.app_name}-cluster"
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${local.app_name}"
  retention_in_days = 14
}

resource "aws_iam_role" "ecs_execution" {
  name = "${local.app_name}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "${local.app_name}-ecs-execution-secrets"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_db_instance.postgres.master_user_secret[0].secret_arn,
          aws_secretsmanager_secret.django_secret_key.arn,
          data.aws_secretsmanager_secret.notify_api_key.arn
        ]
      }
    ]
  })
}

resource "aws_ecs_task_definition" "app" {
  family                   = local.app_name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([
    {
      name      = local.app_name
      image     = "${aws_ecr_repository.app.repository_url}:${var.image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = 8001
          hostPort      = 8001
        }
      ]

      environment = [
        { name = "ALLOWED_HOSTS", value = "${var.app_domain_name} ${aws_lb.app.dns_name}"},
        { name = "DB_HOST", value = aws_db_instance.postgres.address },
        { name = "DB_NAME", value = aws_db_instance.postgres.db_name },
        { name = "DB_USER", value = aws_db_instance.postgres.username },
        { name = "PORT", value = "8001" },
        { name = "AWS_REGION", value = "eu-west-2" },
        { name = "COPILOT_APPLICATION_NAME", value = "ampapp" },
        { name = "COPILOT_ENVIRONMENT_NAME", value = var.environment },
        { name = "COPILOT_SERVICE_NAME", value = "amp-svc" },
        { name = "COPILOT_SERVICE_DISCOVERY_ENDPOINT", value = "${var.environment}.ampapp.local" },
        { name = "AMP_PROTOCOL", value = "https://" },
        { name = "TERRAFORM", value = "TRUE" },
        { name = "BUCKET_NAME", value = aws_s3_bucket.app_files.bucket },
        { name = "AWS_S3_REGION_NAME", value = "eu-west-2" },
        { name = "AMP_VIEWER_DOMAIN", value = var.app_two_domain_name },
      ]

      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = "${aws_db_instance.postgres.master_user_secret[0].secret_arn}"
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
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "app" {
  name             = local.app_name
  cluster          = aws_ecs_cluster.main.id
  task_definition  = aws_ecs_task_definition.app.arn
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
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = local.app_name
    container_port   = 8001
  }

  depends_on = [aws_lb_listener.https]
}

resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_exec_ssm" {
  name = "${local.app_name}-ecs-exec-ssm"
  role = aws_iam_role.ecs_task.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ]
        Resource = "*"
      }
    ]
  })
}