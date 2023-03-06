# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
from botocore.exceptions import ClientError
import json
import os

# print(os.getenv("COPILOT_LB_DNS"))
# if os.getenv("COPILOT_LB_DNS"):
#     print("true")
# else:
#     print("false")
def get_secret():

    secret_name = "amp/to-delete"
    region_name = "eu-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    secret_arn = 'arn:aws:secretsmanager:eu-west-2:144664177605:secret:rds!db-4133af54-2baf-473c-888c-19e769b7a599-k1cyKh'
    auth_token = client.get_secret_value(SecretId=secret_arn).get('SecretString')
    print(auth_token)
    # try:
    #     get_secret_value_response = client.get_secret_value(
    #         SecretId=secret_name
    #     )
    # except ClientError as e:
    #     # For a list of exceptions thrown, see
    #     # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    #     raise e

    # # Decrypts secret using the associated KMS key.
    # secret = get_secret_value_response['SecretString']
    # print(secret)
    # json_acceptable_string = secret.replace("'", "\"")
    # d = json.loads(json_acceptable_string)
    # json_acceptable_string: str = secret.replace("'", "\"")
    # db_credentials = json.loads(json_acceptable_string)
    # s = (
    #     """postgres://"""
    #     f"""{db_credentials["username"]}:"""
    #     f"""{db_credentials["password"]}@"""
    #     f"""{db_credentials["host"]}:"""
    #     f"""{db_credentials["port"]}/accessibility_monitoring_app"""
    # )
    # print(s)
    # s3 = boto3.resource('s3')
    # for bucket in s3.buckets.all():
    #     print(bucket.name)
    # # d = {u'muffin': u'lolz', u'foo': u'kitty'})
    # # Your code goes here.

get_secret()
