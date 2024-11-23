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


@dataclass
class ValueWithSource:
    value: dict
    source: str


def generate_host_file(host: Path, metadata: MetadataVars) -> str:
    """Generate the content of a host file based on the provided metadata."""
    host_vars = load_yaml_cached(host)
    if "metadata" not in host_vars:
        logger.warning(f"Host {host.stem} has no metadata")
        host_vars["metadata"] = {}

    host_vars_struct: dict[str, ValueWithSource] = {}

    with TemporaryFile("w+") as f:
        for metadata_type, metadata_value in host_vars["metadata"].items():
            if isinstance(metadata_value, str):
                logger.debug(f"Processing metadata {metadata_type}/{metadata_value}")
                source = f"{metadata_type}/{metadata_value}"
                if metadata.lookup(metadata_type, host_vars["metadata"][metadata_type]):
                    for k, v in metadata.lookup(
                        metadata_type, host_vars["metadata"][metadata_type]
                    ).items():
                        host_vars_struct[k] = ValueWithSource(v, source)
            elif isinstance(metadata_value, list):
                for item in metadata_value:
                    logger.debug(f"Processing metadata {metadata_type}/{item}")
                    source = f"{metadata_type}/{item}"
                    if metadata.lookup(metadata_type, item):
                        for k, v in metadata.lookup(metadata_type, item).items():
                            host_vars_struct[k] = ValueWithSource(v, source)
            else:
                raise ValueError(
                    f"Invalid metadata type {type(metadata_value)} ({metadata_type}/{metadata_value})"
                )

        source = f"hosts/{host.stem}"
        for k, v in host_vars.items():
            host_vars_struct[k] = ValueWithSource(v, source)

        previous_source: str | None = None
        for k, v in host_vars_struct.items():
            if previous_source is None:
                f.write(f"# {v.source}\n")
                previous_source = v.source
            elif previous_source != v.source:
                f.write(f"\n# {v.source}\n")
                previous_source = v.source

            save_yaml(f, {k: v.value})

        # Test if generated file is valid yaml
        try:
            load_yaml_cached(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Error reading generated file for host {host.stem}: {e}")

        f.seek(0)
        return f.read()


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
