from io import TextIOWrapper
from dagi.logging import logger
from pathlib import Path
import yaml
from functools import lru_cache

try:
    from yaml import CSafeLoader as SafeLoader
    from yaml import CSafeDumper as SafeDumper
except ImportError as e:
    logger.error(e)
    from yaml import SafeLoader, SafeDumper


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
