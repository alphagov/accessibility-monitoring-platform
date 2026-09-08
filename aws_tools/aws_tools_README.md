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
