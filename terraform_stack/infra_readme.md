# GDS Accessibility Monitoring Platform Infrastructure

The infrastructure code for the Accessibility Monitoring Platform is mostly self-contained within this repository.

This README provides a brief overview of how the platform is set up, how Terraform is used, how the CI/CD pipeline works, and other useful functions.

## Contents

- [Infrastructure](#infrastructure)

- [Terraform](#terraform)

- [Prototypes](#prototypes)

- [CI/CD pipeline](#cicd-pipeline)

- [Manual backup](#manual-backup)

- [Resetting the test environment data](#resetting-the-test-environment-data)

- [Viewing production logs](#viewing-production-logs)

- [Alerts](#alerts)


## Infrastructure

The core infrastructure is designed to be as simple as possible. It consists of four main components:

- The Monitoring Platform (ECS)
- The Report Viewer (ECS)
- A PostgreSQL database (RDS)
- An S3 document store

The Monitoring Platform and Report Viewer do not interact directly, but both have access to the same PostgreSQL database and S3 bucket.

The primary S3 bucket serves several purposes, including:

- Storing and serving reports
- Allowing auditors to upload files
- Storing backups of the database

There is also supporting infrastructure used to operate and monitor the platform:

- An additional S3 bucket that is synchronised with the primary S3 bucket for backup purposes
- An S3 bucket that stores load balancer logs, which can be queried using Athena
- AWS WAF, with its logs stored in a separate S3 bucket, which can also be queried using Athena
- A Lambda function that queries the load balancer logs and sends email alerts for HTTP 500 errors
- A CloudWatch dashboard

## Terraform

The entire infrastructure stack is managed with Terraform. The Terraform files are located in `./terraform_stack`.

Deployment helper scripts are located in `./terraform_stack/terraform_deploy`, with the primary script being `terraform_deployment.py`.

Deployments to production, staging and test are managed through the CI/CD pipeline. There are also make commands for managing prototype deployments, so it is rarely necessary to call the deployment script directly.

## Prototypes

`terraform_deployment.py` allows developers to deploy a prototype to AWS based on their current branch. Prototypes are intended to make it easier for developers to share work with the wider team and gather feedback.

To deploy a prototype, first set your temporary AWS credentials for the test account:

```
python aws_tools/aws_2fa.py [test-aws-account] [nnnnnn]
```

Then run:

```
make terraform_deploy_prototype
```

This deploys your current branch as a new Terraform environment in AWS, populated with a backup of production data.

Users can log in using their production environment credentials or create a temporary account with new login details.

A temporary account can be created at any time using:

```
make terraform_create_account_prototype
```

Running `make terraform_deploy_prototype` again updates an existing prototype.

Once you are finished with the prototype, it can be decommissioned with:

```
make terraform_breakdown_prototype
```

The deployment process takes around 30 minutes. Decommissioning takes up to 15 minutes.

## CI/CD pipeline

The CI/CD pipeline is managed entirely through workflows in `.github/workflows`.

`tests.yml` runs unit and end-to-end (E2E) tests when a pull request is created.

`deploy-to-test.yml` runs the same unit and E2E tests when changes are pushed to `dev`. It then deploys the test environment and runs smoke tests.

`deploy-to-prod.yml` runs the unit and E2E tests before performing the full deployment process:

- Backs up the database and uploads the backup to S3
- Checks that the database backup completed successfully before continuing
- Synchronises the S3 bucket with a separate, isolated backup S3 bucket
- Resets staging so that it mirrors production
- Deploys to staging
- Runs smoke tests to verify the staging deployment
- Deploys to production
- Runs smoke tests to verify the production deployment

Production deployment runs nightly. Merging into `main` does not trigger an immediate deployment, reducing the risk of an outage during the working day.

## Manual backup

A manual production backup can be useful when troubleshooting an outage. To create one, run:

```
python terraform_stack/terraform_deploy/terraform_deployment.py --environment prod --function exec --command "python terraform_stack/terraform_deploy/dump_rds_to_s3_as_sql.py" && \
python terraform_stack/terraform_deploy/check_for_s3_backup.py
```

After creating the backup, you can recreate the current production state locally for troubleshooting:

```
git checkout main
git pull
make clean_local
make init
```

## Resetting the test environment data

The data in the test environment does not get updated automatically. To update the test data, run:

```
git checkout dev && \
git pull && \
aws s3 sync s3://amp-app-prod-env-prod-env-files/ s3://amp-app-test-env-test-env-files/ && \
python terraform_stack/terraform_deploy/terraform_deployment.py --environment test --function exec --command 'python terraform_stack/terraform_deploy/prod_deploy_tools.py' && \
python terraform_stack/terraform_deploy/terraform_deployment.py --environment test --function up
```

## Viewing production logs 

To retrieve the previous day's production logs locally, run:

```
make prod_logs_one_day
```

## Alerts

There are currently two alerts in Simple Notification Service (SNS) that developers should subscribe to.

First, `500_errors_platform` sends a daily summary of 40x errors, along with immediate alerts for 500 errors. This is useful for identifying unusually high request volumes and spotting application errors.

Second, `amp-app-prod-env-ecs-deployment-failures` sends alerts when an ECS container fails to start.