import subprocess

import boto3
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):  # pylint: disable=unused-argument
        git_branch_name: str = subprocess.check_output(
            [
                "git",
                "branch",
                "--show-current",
            ]
        ).decode("utf-8")
        git_branch_prefix: str = "".join(e for e in git_branch_name if e.isalnum())[:4]
        app_name: str = f"app{git_branch_prefix}"
        env_name: str = f"env{git_branch_prefix}"

        s3 = boto3.client("s3")
        response = s3.list_buckets()
        buckets = response["Buckets"]

        filtered_buckets = [
            bucket["Name"]
            for bucket in buckets
            if app_name in bucket["Name"] and env_name in bucket["Name"]
        ]
        if filtered_buckets == []:
            raise Exception("No buckets matching the current branch and prototype")

        prototype_bucket_name = filtered_buckets[0]

        subprocess.run(
            [
                "aws",
                "s3",
                "sync",
                "s3://amp-google-drive-platform-files-backup/google-drive-case-files/",
                f"s3://{prototype_bucket_name}/google-drive-case-files/",
            ],
            capture_output=True,
            text=True,
        )

        print(">>> sync complete")
        print(
            """Run: copilot svc exec -a INSERT_APP_NAME -e INSERT_ENV_NAME -n amp-svc --command "python manage.py load_google_drive_files" """
        )
