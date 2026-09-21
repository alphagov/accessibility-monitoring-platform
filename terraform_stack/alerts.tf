resource "aws_sns_topic" "ecs_deployment_failures" {
  name = "${local.app_name}-ecs-deployment-failures"
}


resource "aws_cloudwatch_event_rule" "ecs_deployment_failed" {
  name        = "${local.app_name}-ecs-deployment-failed"
  description = "Notify when an ECS deployment fails"

  event_pattern = jsonencode({
    source = [
      "aws.ecs"
    ]

    "detail-type" = [
      "ECS Deployment State Change"
    ]

    detail = {
      eventName = [
        "SERVICE_DEPLOYMENT_FAILED"
      ]
    }

    resources = [
      aws_ecs_service.app.id,
      aws_ecs_service.viewer.id
    ]
  })
}


resource "aws_cloudwatch_event_target" "ecs_deployment_failed" {
  rule      = aws_cloudwatch_event_rule.ecs_deployment_failed.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.ecs_deployment_failures.arn

  input_transformer {
    input_paths = {
      service_arn   = "$.resources[0]"
      cluster_arn   = "$.detail.clusterArn"
      deployment_id = "$.detail.deploymentId"
      region        = "$.region"
      reason        = "$.detail.reason"
    }

      input_template = <<EOF
"ECS deployment failed"
""
"Service: <service_arn>"
"Cluster: <cluster_arn>"
"Deployment: <deployment_id>"
"Region: <region>"
""
"Reason:"
"<reason>"
EOF
  }
}


data "aws_iam_policy_document" "ecs_deployment_failures" {
  statement {
    effect = "Allow"

    principals {
      type = "Service"

      identifiers = [
        "events.amazonaws.com"
      ]
    }

    actions = [
      "SNS:Publish"
    ]

    resources = [
      aws_sns_topic.ecs_deployment_failures.arn
    ]
  }
}


resource "aws_sns_topic_policy" "ecs_deployment_failures" {
  arn    = aws_sns_topic.ecs_deployment_failures.arn
  policy = data.aws_iam_policy_document.ecs_deployment_failures.json
}