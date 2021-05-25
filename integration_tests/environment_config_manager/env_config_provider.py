import boto3
import os
import json
import logging
from integration_tests.environment_config_manager.env_config_parser import EnvConfigParser


class EnvConfigProvider:
    def __init__(self, workspace_name: str):
        # self.session = session
        self.workspace_name = workspace_name
        self.config_file_path = os.sep.join(
            [os.path.dirname(os.path.realpath(__file__)), "terraform.tfstate"]
        )
        self.logger = logging.getLogger("EnvConfigProvider")
        self.logger.info(f"EnvConfigProvider - workspace: {self.workspace_name}")

    def get_configuration(self) -> EnvConfigParser:
        self._download_config_file()
        with open(self.config_file_path) as json_file:
            config = json.load(json_file)

        return EnvConfigParser(config["resources"])

    def _download_config_file(self) -> None:
        s3 = boto3.client("s3")
        s3.download_file(
            "tf-state-manager",
            f"face-blurer/{self.workspace_name}/terraform.tfstate",
            self.config_file_path,
        )

    def cleanup(self) -> None:
        os.remove(self.config_file_path)
