import argparse
import configparser
import os

import boto3


def main(user: str, mfa_token: str):
    credentials_path: str = f"{os.path.expanduser('~/.aws/')}credentials"

    config = configparser.ConfigParser()
    config.sections()
    config.read(credentials_path)

    if user not in config:
        raise Exception("User does not exist in credentials")

    iam_client = boto3.client(
        "iam",
        aws_access_key_id=config[user]["aws_access_key_id"],
        aws_secret_access_key=config[user]["aws_secret_access_key"],
        region_name="eu-west-2",
    )

    iam_response = iam_client.list_mfa_devices()

    if len(iam_response["MFADevices"]) > 1:
        for n, device in enumerate(iam_response["MFADevices"]):
            print(f"""#{n+1}: SerialNumber - {device["SerialNumber"]} | EnableDate: {str(device["EnableDate"])}""")

        while True:
            print("Pick which MFA device you want to use:")
            option = input()
            if option.isdigit() is False:
                print("Please input a number...")
            elif int(option) > len(iam_response["MFADevices"]):
                print(f"{option} is greater than the number of options. Please select from the options provided...")
            elif int(option) <= 0:
                print("Please input a positive integer...")
            else:
                option = int(option) - 1
                print(f""">>> Selected {iam_response["MFADevices"][option]["SerialNumber"]}""")
                serial_number: str = iam_response["MFADevices"][option]["SerialNumber"]
                break
    else:
        serial_number: str = iam_response["MFADevices"][0]["SerialNumber"]

    sts_client = boto3.client(
        "sts",
        aws_access_key_id=config[user]["aws_access_key_id"],
        aws_secret_access_key=config[user]["aws_secret_access_key"],
        region_name="eu-west-2",
    )

    sts_response = sts_client.get_session_token(
        SerialNumber=serial_number,
        TokenCode=mfa_token,
    )

    config["mfa"] = {
        "aws_access_key_id": sts_response["Credentials"]["AccessKeyId"],
        "aws_secret_access_key": sts_response["Credentials"]["SecretAccessKey"],
        "aws_session_token": sts_response["Credentials"]["SessionToken"],
        "region": "eu-west-2",
    }

    with open(credentials_path, "w", encoding="utf-8") as configfile:
        config.write(configfile)

    print(">>> Saved MFA credentials under mfa profile")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Set AWS session credentials for user",
        epilog="Stores session credentials in ~/.aws/credentials as profile [mfa]",
    )
    parser.add_argument("user", help="AWS user to set session credentials for")
    parser.add_argument("mfa_token", help="Time-based one-time token for AWS user")
    args = parser.parse_args()

    main(user=args.user, mfa_token=args.mfa_token)
