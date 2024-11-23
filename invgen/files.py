from io import TextIOWrapper
from invgen.logging import logger
from pathlib import Path
import yaml
from functools import lru_cache

try:
    from yaml import CSafeLoader as SafeLoader
    from yaml import CSafeDumper as SafeDumper
except ImportError as e:
    logger.error(e)
    from yaml import SafeLoader, SafeDumper


class VaultPass(str):
    """String subclass to represent vault-encrypted values"""

    pass


def ansible_vault_constructor(loader, node: yaml.nodes.ScalarNode) -> VaultPass:
    """Construct a VaultPass object from a YAML node"""
    if not isinstance(node, yaml.ScalarNode):
        raise yaml.constructor.ConstructorError(
            None, None, f"expected a scalar node, but found {node.id}", node.start_mark
        )
    return VaultPass(loader.construct_scalar(node))


def ansible_vault_representer(dumper, data: VaultPass) -> yaml.nodes.ScalarNode:
    """Represent a VaultPass object as a YAML scalar node"""
    return dumper.represent_scalar(
        "!vault",
        str(data),
        style="|",  # Use literal block style for multiline vault strings
    )


# Register the custom constructor and representer
SafeLoader.add_constructor("!vault", ansible_vault_constructor)
SafeDumper.add_representer(VaultPass, ansible_vault_representer)


@lru_cache
def load_yaml_cached(file: Path) -> dict:
    """Load a yaml file and cache the result"""
    return load_yaml(file)


def load_yaml(file: Path | TextIOWrapper) -> dict:
    """Load a yaml file"""
    try:
        if isinstance(file, Path):
            return yaml.load(file.read_text(), Loader=SafeLoader)
        else:
            return yaml.load(file.read(), Loader=SafeLoader)
    except (yaml.YAMLError, OSError) as e:
        logger.error(f"Error processing file: {e}")
        raise


def save_yaml(file: Path | TextIOWrapper, data: dict, sort_keys: bool = False) -> None:
    """Save a yaml file"""
    try:
        content = yaml.dump(
            data,
            Dumper=SafeDumper,
            sort_keys=sort_keys,
            indent=2,
            default_flow_style=False,
            allow_unicode=True,
        )
        if isinstance(file, Path):
            file.write_text(content)
        else:
            file.write(content)
    except (yaml.YAMLError, OSError) as e:
        logger.error(f"Error processing file: {e}")
        raise
