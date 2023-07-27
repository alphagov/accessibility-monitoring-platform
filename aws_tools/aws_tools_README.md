# AWS Tools


## Index 

- [Requirements](#Requirements)
- [aws_2fa.py](#aws_2fa.py)
- [dump_rds_to_s3_as_sql.py](#dump_rds_to_s3_as_sql.py)
- [reset_staging_db.py](#reset_staging_db.py)
- [How to gain access to Copilot database](#How-to-gain-access-to-Copilot-database)

## Requirements

- AWS CLI

## aws_2fa.py

Used to set up `mfa` profile in ~/.aws/credentials

The command line args require `AWS profile` and `2FA code`

`python aws_tools/aws_2fa.py [PROFILE] [2FA code]`

e.g.

`python aws_tools/aws_2fa.py default 123456`

N.B: If you use MFA for AWS services, ensure AWS_PROFILE is configured correctly to use the `mfa` profile.

It is recommended to change the default AWS_PROFILE by executing `export AWS_PROFILE=mfa` in the command line or adding `export AWS_PROFILE=mfa` to ~/.bashrc or ~/.zshrc. Changing the AWS_PROFILE will ensure AWS CLI and Boto3 use the MFA profile as default when accessing any AWS service.

## dump_rds_to_s3_as_sql.py

Used internally in ECS to backup the database to S3. Triggered during the deployment to production.

## reset_staging_db.py

Used internally in ECS to load the production database into the staging database. Triggered during the deployment to production.

## How to gain access to Copilot database

To gain access to a Copilot DB, you have to exec into an ECS instance. The command for doing this is:

`copilot svc exec -a APPNAME -e ENVNAME -n SVCNAME`

As an example, to exec into the amp service in testing, the command would be:

`copilot svc exec -a ampapp -e testenv -n amp-svc`

Once you're inside the ECS instance, you can connect to the postgres instance using PSQL. To get the databse credentials, you can use `printenv DB_SECRET`.

With the credentials to hand, you can access PSQL with following command

`psql -h HOST -U USERNAME -p 5432 accessibility_monitoring_app`

Enter the password found in `printenv DB_SECRET` and you should now have access to the databse.

In depth documentation can be found [in the Copilot documentation](https://aws.github.io/copilot-cli/docs/commands/svc-exec/)
