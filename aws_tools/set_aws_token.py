import boto3
import configparser
import os
import sys

if __name__ == "__main__":
    user: str = sys.argv[1]
    cred_file: str = f"{os.path.expanduser('~/.aws/')}credentials"

    config = configparser.ConfigParser()
    config.sections()
    config.read(cred_file)
    if user not in config:
        raise Exception("User does not exist in credentials")
    iam_client = boto3.client(
        "iam",
        aws_access_key_id=config[user]["aws_access_key_id"],
        aws_secret_access_key=config[user]["aws_secret_access_key"],
        region_name="eu-west-2"
    )
    response = iam_client.list_mfa_devices()
    serial_number: str = response["MFADevices"][0]["SerialNumber"]
    sts_client = boto3.client(
        "sts",
        aws_access_key_id=config[user]["aws_access_key_id"],
        aws_secret_access_key=config[user]["aws_secret_access_key"],
        region_name="eu-west-2"
    )
    response = sts_client.get_session_token(
        SerialNumber=serial_number,
        TokenCode=sys.argv[2]
    )

    config["mfa"] = {
        "aws_access_key_id": response["Credentials"]["AccessKeyId"],
        "aws_secret_access_key": response["Credentials"]["SecretAccessKey"],
        "aws_session_token": response["Credentials"]["SessionToken"],
        "region": "eu-west-2",
    }
    with open(cred_file, "w", encoding="utf-8") as configfile:
        config.write(configfile)

    print(">>> Saved MFA credentials under mfa profile")
