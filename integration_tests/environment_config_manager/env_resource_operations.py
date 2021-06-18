import time
import boto3
import os
import logging
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


def check_if_files_exist_in_bucket(
    bucket_name: str,
    path: str,
    files_to_check: list,
    wait_interval: int = 5,
    attempts: int = 30,
) -> bool:
    logger.info(
        f"S3 - {bucket_name} = interval {wait_interval}sec and {attempts} attempts"
    )
    client = boto3.client("s3")

    invoke_counter = 0

    while invoke_counter < attempts:
        logger.info(f"#{invoke_counter+1} looking for files in {bucket_name}")

        response = client.list_objects_v2(Bucket=bucket_name, Prefix=path)
        if "Contents" in response.keys():
            logger.info(f"S3 bucket: {response['Contents']}")
            files_in_bucket = [
                file_content["Key"] for file_content in response["Contents"]
            ]
            if all(
                (
                    os.path.join(path, file_name) in files_in_bucket
                    for file_name in files_to_check
                )
            ):
                return True

        time.sleep(wait_interval)
        invoke_counter += 1

    return False


def upload_file(file_name: str, bucket: str, object_name: str) -> bool:
    logger.info(f"Uploading file {file_name} to {bucket}/{object_name}")
    s3_client = boto3.client("s3")
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True
