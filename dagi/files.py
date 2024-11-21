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


def load_yaml(file: Path) -> dict:
    """Load a yaml file"""
    try:
        return yaml.load(file.read_text(), Loader=SafeLoader)
    except (yaml.YAMLError, OSError) as e:
        logger.error(f"Error processing file: {e}")
        raise


def save_yaml(file: Path, data: dict) -> None:
    """Save a yaml file"""
    try:
        file.write_text(yaml.dump(data, Dumper=SafeDumper))
    except (yaml.YAMLError, OSError) as e:
        logger.error(f"Error processing file: {e}")
        raise
