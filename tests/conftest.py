import sys
import os
import boto3
import moto
import pytest
import tempfile


def pytest_sessionstart():
    sys.path.extend([os.path.join(os.path.dirname(__file__), "../src")])


@pytest.fixture
def env_variables(monkeypatch):
    monkeypatch.setenv("destination_bucket", "face-blurer-destination")


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        old_work_dir = os.getcwd()
        os.chdir(tmp_dir_name)

        yield tmp_dir_name

        os.chdir(old_work_dir)


@pytest.fixture
def destination_bucket():
    bucket_name = "face-blurer-destination"
    with moto.mock_s3() as mock:
        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=bucket_name)

        s3 = boto3.client("s3")

        def add_file_to_bucket(file_path, content=None):
            s3.put_object(
                Bucket=bucket_name,
                Key=f"{file_path}",
                Body=content if content is not None else file_path,
            )

        yield mock, add_file_to_bucket, bucket_name


@pytest.fixture
def origin_bucket():
    bucket_name = "face-blurer-origin"
    with moto.mock_s3() as mock:
        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=bucket_name)

        s3 = boto3.client("s3")

        def add_file_to_bucket(file_path, content=None):
            s3.put_object(
                Bucket=bucket_name,
                Key=f"{file_path}",
                Body=content if content is not None else file_path,
            )

        yield mock, add_file_to_bucket, bucket_name
