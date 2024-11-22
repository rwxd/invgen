from typing import Any
import json


class AnsibleInventory:
    def __init__(self, hosts):
        self.hosts = hosts

    def build_groups(self) -> dict[str, list[str]]:
        return {}

    def build(self) -> dict[str, Any]:
        """Builds the inventory"""
        groups = self.build_groups()

        return {
            "_meta": {"hostvars": {}},
            "all": {"children": list(groups.keys())},
            **groups,
        }

    def render(self, pretty: bool = False) -> str:
        """Renders the inventory as json"""
        if pretty:
            return json.dumps(self.build(), indent=2)
        return json.dumps(self.build())

    def __str__(self):
        return str(self.hosts)
