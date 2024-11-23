from dataclasses import dataclass, field
from pathlib import Path
from invgen.files import load_yaml_cached
from invgen.logging import logger


@dataclass()
class MetadataVars:
    customer: dict[str, dict] = field(default_factory=dict)
    os: dict[str, dict] = field(default_factory=dict)
    environment: dict[str, dict] = field(default_factory=dict)
    location: dict[str, dict] = field(default_factory=dict)
    services: dict[str, dict] = field(default_factory=dict)
    groups: dict[str, dict] = field(default_factory=dict)
    tags: dict[str, dict] = field(default_factory=dict)

    def lookup(self, metadata: str, key: str) -> dict:
        """
        Lookup metadata key in metadata vars

        raises ValueError if metadata or key not foun
        """

        logger.debug(f"Looking up metadata {metadata} key {key}")
        try:
            sub_metadata = dict(getattr(self, metadata))
        except AttributeError:
            raise ValueError(f"Metadata {metadata} not found")

        result = sub_metadata.get(key, {})
        if not result:
            logger.warning(f"Metadata {metadata} key {key} not found")

        return result


def build_metadata_vars(data_dir: Path) -> MetadataVars:
    vars = MetadataVars()
    logger.info("Getting metadata vars")
    for file in data_dir.joinpath("metadata/customer/").rglob("*.yaml"):
        vars.customer[file.stem] = load_yaml_cached(file)
    for file in data_dir.joinpath("metadata/os/").rglob("*.yaml"):
        vars.os[file.stem] = load_yaml_cached(file)
    for file in data_dir.joinpath("metadata/environment/").rglob("*.yaml"):
        vars.environment[file.stem] = load_yaml_cached(file)
    for file in data_dir.joinpath("metadata/location/").rglob("*.yaml"):
        vars.location[file.stem] = load_yaml_cached(file)
    for file in data_dir.joinpath("metadata/services/").rglob("*.yaml"):
        vars.services[file.stem] = load_yaml_cached(file)
    for file in data_dir.joinpath("metadata/groups/").rglob("*.yaml"):
        vars.groups[file.stem] = load_yaml_cached(file)
    for file in data_dir.joinpath("metadata/tags/").rglob("*.yaml"):
        vars.tags[file.stem] = load_yaml_cached(file)
    return vars
