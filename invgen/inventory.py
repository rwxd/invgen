import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer

from invgen.hosts import GeneratedHost, get_all_generated_hosts
from invgen.logging import init_logger, logger


@dataclass
class Group:
    name: str
    hosts: list[str]


class AnsibleInventory:
    def __init__(self, hosts: list[GeneratedHost]):
        self.hosts = hosts

    def _build_groups(self) -> list[Group]:
        group_filter: dict[str, list[str]] = defaultdict(list)

        for host in self.hosts:
            if "metadata" in host.vars:
                for k, v in host.vars["metadata"].items():
                    if isinstance(v, list):
                        for item in v:
                            group_filter[f"{k}_{item}"].append(host.name)
                    elif isinstance(v, str):
                        group_filter[f"{k}_{v}"].append(host.name)
                    else:
                        logger.warning(
                            f"Invalid metadata type {type(v)} ({k}/{v}) on {host.name}"
                        )
            else:
                logger.warning(f"Host {host.name} has no metadata")
                group_filter["ungrouped"].append(host.name)

        groups = [Group(name=k, hosts=v) for k, v in group_filter.items()]
        return groups

    def _build_hostvars(self) -> dict[str, dict[str, Any]]:
        return {host.name: host.vars for host in self.hosts}

    def build(self) -> dict[str, Any]:
        """Builds the inventory"""
        groups = self._build_groups()
        inventory: dict[str, Any] = {}
        inventory["_meta"] = {"hostvars": self._build_hostvars()}
        all_hosts = set()

        for group in groups:
            inventory[group.name] = {"hosts": group.hosts}
            all_hosts.update(group.hosts)

        inventory["all"] = {"hosts": list(all_hosts)}
        return inventory

    def render(self, pretty: bool = False) -> str:
        """Renders the inventory as json"""
        if pretty:
            return json.dumps(self.build(), indent=2)

        return json.dumps(self.build())

    def build_host(self, host: str) -> dict[str, Any]:
        """Builds hostvars for a specific host"""
        hostvars = self._build_hostvars()
        return hostvars.get(host, {})

    def render_host(self, host: str, pretty: bool = False) -> str:
        if pretty:
            return json.dumps(self.build_host(host), indent=2)
        return json.dumps(self.build_host(host))

    def __str__(self):
        return str(self.hosts)


inventory_app = typer.Typer()


@inventory_app.command()
def inventory(
    source: Path = typer.Option(
        Path().cwd(), envvar="INVGEN_SOURCE", help="Source directory"
    ),
    pretty: bool = False,
    list_hosts: bool = typer.Option(False, "--list", help="Output inventory"),
    host: str = typer.Option("", "--host", help="Output hostvars for a host"),
    log_level: str = typer.Option("INFO", help="Log level"),
):
    init_logger(log_level)

    logger.info(f"Generating inventory from {source}")
    hosts = get_all_generated_hosts(source)
    inventory = AnsibleInventory(hosts)

    if list_hosts:
        print(inventory.render(pretty=pretty))
    elif len(host) > 0:
        print(inventory.render_host(host, pretty=pretty))
    else:
        typer.echo("No command specified (--host or --list)", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    inventory_app()
