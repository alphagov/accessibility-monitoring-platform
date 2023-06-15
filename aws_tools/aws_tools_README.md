# AWS Tools


## Index 

- [Requirements](#Requirements)
- [aws_2fa.py](#aws_2fa.py)
- [aws_copilot_setup.py](#aws_copilot_setup.py)
- [aws_reset_db.py](#aws_reset_db.py)
- [aws_upload_db_backup.py](#aws_upload_db_backup.py)
- [restore_db_aws.py](#restore_db_aws.py)
- [set_aws_token.py](#set_aws_token.py)
- [transfer_s3_contents.py](#transfer_s3_contents.py)
- [Other commands](#Other-commands)
- [What to do when a Copilot deployment continually fails](#What-to-do-when-a-Copilot-deployment-continually-fails)

---

## Requirements

- Cloud Foundry account
- Access to test AWS environment
- Copilot CLI

---

## aws_2fa.py

Used to set up `mfa` profile in ~/.aws/credentials

The command line args require `AWS profile` and `2FA code`

`python aws_tools/aws_2fa.py [PROFILE] [2FA code]`

e.g.

`python aws_tools/aws_2fa.py default 123456`

N.B: If you use MFA for AWS services, ensure AWS_PROFILE is configured correctly to use the `mfa` profile.

It is possible to change the default AWS_PROFILE by executing `export AWS_PROFILE=mfa` in the command line or adding `export AWS_PROFILE=mfa` to ~/.bashrc or ~/.zshrc. Changing the AWS_PROFILE will ensure AWS CLI and Boto3 use the MFA profile as default when accessing any AWS service.

---

## aws_copilot_setup.py

Used to create or delete an entire Copilot app from scratch.

To build a new app from scratch, use `python aws_tools/aws_copilot_setup.py --build-direction up`

To breakdown the same environment, use `python aws_tools/aws_copilot_setup.py --build-direction down`

The script includes the commands to start a new Copilot app and may be helpful to learn how to create a new Copilot app step-by-step.

N.B. Starting a new Copilot app can take over 60 minutes and breaking down a Copilot app can take up to 30 minutes.

---

## aws_reset_db.py

A script made to execute inside an ECS instance to wipe and create a clean db inside Aurora Postgres. Not to be used locally.

Can either use `copilot svc exec -a amp-app -e prod-env -n amp-svc --command "python aws_tools/aws_reset_db.py"` or `make wipe_aurora_db` to start it

---

## aws_upload_db_backup.py

A script made to execute inside an ECS instance. Downloads a database from S3 and restores the Aurora Postgres database. Not to be used locally.

---

## restore_db_aws.py

End-to-end script for transferring the production DB in CF to AWS. It can be started with `python aws_tools/restore_db_aws.py`.

---

## set_aws_token.py

Alternative script to aws_2fa.py

---

## transfer_s3_contents.py

Takes files from the S3 bucket inside CF and transfers them to the Copilot S3 bucket.

Ensure `AWS_ACCESS_KEY_ID_S3_STORE` and `AWS_SECRET_ACCESS_KEY_S3_STORE` is set in the `.env` file with the Cloud Foundry S3 bucket access credentials. 

---

## Other commands

`make wipe_aurora_db` wipes and creates a clean DB in Aurora Postgres

`make restore_db_aws` restores an Aurora Postgres DB and S3 bucket with production data

`make deploy_amp` deploys monitoring platform to ECS

`make deploy_viewer` deploys viewer app to ECS

`make delete_amp` deletes monitoring platform on ECS

`make delete_viewer` deletes viewer app on ECS

`make build_amp` builds monitoring platform local Docker image

`make build_viewer` builds viewer app local Docker image

`make run_stack` starts local docker compose


---

## What to do when a Copilot deployment continually fails

When a deployment fails, it will get stuck and will continually try. Exiting the process will not stop it, and Copilot will be inaccessible until it has exhausted retries.

One way to gracefully stop the process is to reduce the `Desired tasks` from 1 to 0.

To do this: 
- Navigate to ECS in the AWS console. 
- Open the Copilot cluster (e.g. amp-app-prod-env-Cluster-Ld6qaysMDEXk)
- Select the service that is 'stuck.'
- Click the `Update service` button in the top right corner
- Change desired tasks from 1 to 0
- Wait for the Copilot deployment to 'finish'