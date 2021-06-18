import pytest
from integration_tests.environment_config_manager.env_config_parser import (
    EnvConfigParser,
)


@pytest.fixture(scope="session")
def buckets_config(environment_config: EnvConfigParser):
    return {
        "origin_bucket": environment_config.get_configuration(
            "aws_s3_bucket", "origin"
        )["bucket"],
        "destination_bucket": environment_config.get_configuration(
            "aws_s3_bucket", "destination"
        )["bucket"],
    }
