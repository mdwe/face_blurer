import pytest
import logging
import tempfile
import os
from integration_tests.environment_config_manager.env_config_provider import EnvConfigProvider


@pytest.fixture(scope="session", autouse=True)
def logger() -> logging.Logger:
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("Integration tests")

    return logger


def pytest_addoption(parser):
    parser.addoption("--environment", action="store", default="test")


@pytest.fixture(scope="session", autouse=True)
def config_arguments(pytestconfig) -> dict:
    return {"environment": pytestconfig.getoption("environment")}


@pytest.fixture(scope="session")
def environment_config(
    logger: logging.Logger, config_arguments: dict
) -> EnvConfigProvider:
    config_provider = EnvConfigProvider(config_arguments["environment"])
    config = config_provider.get_configuration()

    if not config.config:
        config_provider.cleanup()
        pytest.exit("Tfstate file not found for selected workspace...")

    yield config

    logger.info("Environment configuration teardown...")
    config_provider.cleanup()


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        old_work_dir = os.getcwd()
        os.chdir(tmp_dir_name)

        yield tmp_dir_name

        os.chdir(old_work_dir)
