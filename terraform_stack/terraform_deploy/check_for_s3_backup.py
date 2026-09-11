import time
from datetime import datetime, timezone, timedelta

import boto3
from botocore.exceptions import ClientError


def wait_for_recent_s3_object(
    bucket: str,
    prefix: str,
    recent_within_minutes: int = 10,
    timeout_seconds: int = 600,
    initial_poll_seconds: int = 5,
    max_poll_seconds: int = 60,
):
    """
    Wait for an S3 object to appear under `prefix` that was uploaded recently.

    Returns:
        dict: Metadata for the newest qualifying S3 object.

    Raises:
        TimeoutError: If no qualifying object appears before timeout.
        ClientError: For AWS/S3 errors.
    """
    s3 = boto3.client("s3")

    started_at = time.monotonic()
    poll_interval = initial_poll_seconds

    while True:
        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(minutes=recent_within_minutes)

        try:
            paginator = s3.get_paginator("list_objects_v2")

            newest_object = None

            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    if obj["LastModified"] >= recent_cutoff:
                        if (
                            newest_object is None
                            or obj["LastModified"] > newest_object["LastModified"]
                        ):
                            newest_object = obj

            if newest_object:
                print(
                    f"Backup found: s3://{bucket}/{newest_object['Key']} "
                    f"(uploaded {newest_object['LastModified'].isoformat()})"
                )
                return newest_object

        except ClientError as exc:
            print(f"Error checking S3: {exc}")
            raise

        elapsed = time.monotonic() - started_at

        if elapsed >= timeout_seconds:
            raise TimeoutError(
                f"No recent object found in s3://{bucket}/{prefix} "
                f"after {timeout_seconds} seconds."
            )

        remaining = timeout_seconds - elapsed
        sleep_for = min(poll_interval, remaining)

        print(
            f"No backup found yet. Checking again in "
            f"{sleep_for:.0f} seconds..."
        )

        time.sleep(sleep_for)

        # Exponential backoff, capped at max_poll_seconds.
        poll_interval = min(poll_interval * 2, max_poll_seconds)


if __name__ == "__main__":
    try:
        backup = wait_for_recent_s3_object(
            bucket="amp-app-prod-env-prod-env-files",
            prefix="aws_aurora_backup/",
            recent_within_minutes=12,
            timeout_seconds=60,
            initial_poll_seconds=5,
            max_poll_seconds=60,
        )

        print(f"Backup confirmed: {backup['Key']}")

    except TimeoutError as exc:
        print(exc)
        raise SystemExit(1)