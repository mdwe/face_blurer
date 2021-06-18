from typing import Optional


class EnvConfigParser:
    def __init__(self, config: dict):
        self.config = config

    def get_configuration(
        self, resource_type: str, resource_name: Optional[str] = ""
    ) -> dict:
        for resource in self.config:
            required_condition = (
                resource.get("type") == resource_type
                and resource.get("name") == resource_name
            )

            if required_condition:
                return resource["instances"][0]["attributes"]
        return {}
