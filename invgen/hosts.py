from pathlib import Path
from dataclasses import dataclass
from invgen.files import load_yaml_cached, save_yaml
from tempfile import TemporaryFile

from invgen.metadata import build_metadata_vars, MetadataVars
from invgen.logging import logger
import yaml


def generate_hosts(data_dir: Path):
    metadata = build_metadata_vars(data_dir)
    files = get_all_host_files(data_dir)
    logger.info(f"Generating {len(files)} hosts")
    for host in files:
        logger.info(f"Generating host {host.stem}")
        path = get_generated_host_path(data_dir, host.stem)
        content = generate_host_file(host, metadata)

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)


def generate_host_file(host: Path, metadata: MetadataVars) -> str:
    """Generate the content of a host file based on the provided metadata."""
    host_vars = load_yaml_cached(host)
    validate_host_vars(host.stem, host_vars)

    with TemporaryFile("w+") as f:
        previous_source: str | None = None

        # Iterate over metadata items and dump them to the temporary file
        for key, value in host_vars["metadata"].items():
            if isinstance(value, str):
                logger.debug(f"Processing metadata key: {key}, value: {value}")
                source = f"{key}/{value}.yaml"
                if metadata.lookup(key, host_vars["metadata"][key]):
                    if previous_source != source:
                        f.write(f"\n# {source}\n")
                    save_yaml(f, metadata.lookup(key, host_vars["metadata"][key]))
                    previous_source = source
            elif isinstance(value, list):
                for item in value:
                    logger.debug(f"Processing metadata key: {key}, value: {item}")
                    source = f"{key}/{item}.yaml"
                    if metadata.lookup(key, item):
                        if previous_source != source:
                            f.write(f"\n# {source}\n")
                        save_yaml(f, metadata.lookup(key, item))
                        previous_source = source
            else:
                raise ValueError(f"Invalid metadata type key: {key}")

        # Dump the entire host_vars to the temporary file
        source = f"hosts/{host.stem}.yaml"
        f.write(f"\n# {source}\n")
        save_yaml(f, host_vars)

        # Test if generated file is valid yaml
        try:
            load_yaml_cached(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Error reading generated file for host {host.stem}: {e}")

        f.seek(0)
        return f.read()


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
