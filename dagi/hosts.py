from pathlib import Path
from dataclasses import dataclass
from dagi.files import load_yaml_cached
from tempfile import TemporaryFile

from dagi.metadata import build_metadata_vars, MetadataVars
from dagi.logging import logger
import yaml


try:
    from yaml import CSafeDumper as SafeDumper
except ImportError as e:
    logger.error(e)
    from yaml import SafeDumper


def generate_hosts(data_dir: Path):
    metadata = build_metadata_vars(data_dir)
    files = get_all_host_files(data_dir)
    logger.info(f"Generating {len(files)} hosts")
    for host in files:
        logger.info(f"Generating host {host.stem}")
        path = get_generated_host_path(data_dir, host.stem)
        vars = get_vars_for_host(host, metadata)


def get_vars_for_host(host: Path, metadata: MetadataVars) -> dict:
    host_vars = load_yaml_cached(host)
    validate_host_vars(host.stem, host_vars)

    def _dump(f, key, value):
        yaml.dump(
            {key: value},
            f,
            Dumper=SafeDumper,
            indent=2,
            allow_unicode=True,
            default_flow_style=False,
        )

    with TemporaryFile("w+") as f:
        previous_source: str | None = None
        for key, value in host_vars["metadata"].items():
            if isinstance(key, str):
                source = f"{key}/{value}.yaml"
                if metadata.lookup(key, host_vars["metadata"][key]):
                    if previous_source != source:
                        f.write(f"\n# {source}\n")
                    _dump(f, key, value)
                    previous_source = source
            elif isinstance(key, list):
                for item in key:
                    source = f"{item}/{value}.yaml"
                    if metadata.lookup(item, host_vars["metadata"][item]):
                        if previous_source != source:
                            f.write(f"\n# {source}\n")
                        _dump(f, key, value)
                        previous_source = source
            else:
                raise ValueError(f"Invalid metadata type key: {key}")

    return host_vars


def validate_host_vars(host: str, vars: dict):
    if not vars.get("metadata"):
        raise ValueError(f"Metadata not found for host {host}")
    if "customer" not in vars.get("metadata"):
        raise ValueError(f"Customer metadata not found for host {host}")
    if "os" not in vars.get("metadata"):
        raise ValueError(f"OS metadata not found for host {host}")
    if "environment" not in vars.get("metadata"):
        raise ValueError(f"Environment metadata not found for host {host}")
    if "location" not in vars.get("metadata"):
        raise ValueError(f"Location metadata not found for host {host}")
    if "services" not in vars.get("metadata"):
        raise ValueError(f"Services metadata not found for host {host}")
    if "groups" not in vars.get("metadata"):
        raise ValueError(f"Groups metadata not found for host {host}")
    if "tags" not in vars.get("metadata"):
        raise ValueError(f"Tags metadata not found for host {host}")


def get_generated_host_path(base_dir: Path, host: str) -> Path:
    return base_dir.joinpath(f"generated/{host}.yaml")


def get_all_host_files(base_path: Path) -> list[Path]:
    host_files = base_path.joinpath("hosts/").rglob("*.yaml")
    return [f for f in host_files if f.is_file()]


@dataclass
class GeneratedHost:
    name: str
    vars: dict


def get_all_generated_hosts_files(base_path: Path) -> list[Path]:
    files = base_path.joinpath("generated/").rglob("*.yaml")
    return [f for f in files if f.is_file()]


def get_all_generated_hosts(base_path: Path = Path().cwd()):
    hosts = []
    for file in get_all_generated_hosts_files(base_path):
        if file.is_file():
            hosts.append(GeneratedHost(name=file.stem, vars=load_yaml_cached(file)))
    return hosts
