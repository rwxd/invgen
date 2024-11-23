from pathlib import Path
from invgen.files import load_yaml_cached
from invgen.logging import logger


class MetadataVars:
    def __init__(self):
        self._metadata = {}

    def add_metadata(self, name: str):
        logger.info(f"Adding metadata type {name}")
        self._metadata[name] = {}

    def set_vars(self, metadata_type: str, name: str, vars: dict):
        self._metadata[metadata_type][name] = vars

    def __repr__(self) -> str:
        return f"MetadataVars({self._metadata})"

    def __getattr__(self, name: str):
        if name in self._metadata:
            return self._metadata[name]
        raise AttributeError(f"'MetadataVars' object has no attribute '{name}'")

    def lookup(self, metadata: str, key: str) -> dict:
        """
        raises ValueError if metadata or key not found
        """

        logger.debug(f"Looking up metadata {metadata}/{key}")
        try:
            sub_metadata = dict(getattr(self, metadata))
        except AttributeError:
            raise ValueError(
                f'Metadata type "{metadata}" not found. Consider adding a directory at "metadata/{metadata}"'
            )

        result = sub_metadata.get(key, {})
        if not result:
            logger.warning(
                f"Metadata {metadata}/{key} not found. "
                f'Did you forget to add "{key}.yaml" to "metadata/{metadata}/"?'
            )

        return result


def build_metadata_vars(data_dir: Path) -> MetadataVars:
    vars = MetadataVars()
    logger.info("Getting metadata vars")
    metadata_dir = data_dir.joinpath("metadata")
    for subdir in metadata_dir.iterdir():
        if subdir.is_dir():
            vars.add_metadata(subdir.name)
            for file in subdir.rglob("*.yaml"):
                vars.set_vars(subdir.name, file.stem, load_yaml_cached(file))
    return vars
