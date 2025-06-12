import os
import tempfile
from pathlib import Path

import pytest
import yaml

from invgen.metadata import MetadataVars, build_metadata_vars


@pytest.fixture
def temp_metadata_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create metadata directory structure
        metadata_dir = Path(tmpdir) / "metadata"
        os.makedirs(metadata_dir / "platform")
        os.makedirs(metadata_dir / "environment")
        os.makedirs(metadata_dir / "tags")

        # Create platform metadata files
        with open(metadata_dir / "platform" / "raspberry-pi-4.yaml", "w") as f:
            yaml.dump({"cpu_arch": "arm64", "memory": "4GB"}, f)

        with open(metadata_dir / "platform" / "x86-server.yaml", "w") as f:
            yaml.dump({"cpu_arch": "x86_64", "memory": "16GB"}, f)

        # Create environment metadata files
        with open(metadata_dir / "environment" / "production.yaml", "w") as f:
            yaml.dump({"backup_enabled": True, "monitoring_level": "high"}, f)

        with open(metadata_dir / "environment" / "staging.yaml", "w") as f:
            yaml.dump({"backup_enabled": False, "monitoring_level": "medium"}, f)

        # Create tags metadata files
        with open(metadata_dir / "tags" / "web.yaml", "w") as f:
            yaml.dump({"open_ports": [80, 443], "service_type": "web"}, f)

        with open(metadata_dir / "tags" / "database.yaml", "w") as f:
            yaml.dump({"open_ports": [5432], "service_type": "database"}, f)

        yield Path(tmpdir)


def test_metadata_vars_add_metadata():
    metadata = MetadataVars()
    metadata.add_metadata("platform")
    metadata.add_metadata("environment")

    assert hasattr(metadata, "platform")
    assert hasattr(metadata, "environment")

    with pytest.raises(AttributeError):
        metadata.non_existent


def test_metadata_vars_set_vars():
    metadata = MetadataVars()
    metadata.add_metadata("platform")

    metadata.set_vars("platform", "raspberry-pi-4", {"cpu_arch": "arm64"})

    assert metadata.lookup("platform", "raspberry-pi-4") == {"cpu_arch": "arm64"}


def test_metadata_vars_lookup():
    metadata = MetadataVars()
    metadata.add_metadata("platform")
    metadata.set_vars("platform", "raspberry-pi-4", {"cpu_arch": "arm64"})

    # Test successful lookup
    assert metadata.lookup("platform", "raspberry-pi-4") == {"cpu_arch": "arm64"}

    # Test lookup with non-existent metadata type
    with pytest.raises(ValueError):
        metadata.lookup("non_existent", "raspberry-pi-4")

    # Test lookup with non-existent key
    assert metadata.lookup("platform", "non_existent") == {}


def test_build_metadata_vars(temp_metadata_dir):
    metadata = build_metadata_vars(temp_metadata_dir)

    # Check that all metadata types were loaded
    assert hasattr(metadata, "platform")
    assert hasattr(metadata, "environment")
    assert hasattr(metadata, "tags")

    # Check specific metadata values
    assert metadata.lookup("platform", "raspberry-pi-4") == {
        "cpu_arch": "arm64",
        "memory": "4GB",
    }
    assert metadata.lookup("environment", "production") == {
        "backup_enabled": True,
        "monitoring_level": "high",
    }
    assert metadata.lookup("tags", "web") == {
        "open_ports": [80, 443],
        "service_type": "web",
    }


def test_build_metadata_vars_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create empty metadata directory
        metadata_dir = Path(tmpdir) / "metadata"
        os.makedirs(metadata_dir)

        metadata = build_metadata_vars(Path(tmpdir))

        # Should have no metadata types
        assert not hasattr(metadata, "platform")
        assert not hasattr(metadata, "environment")


def test_build_metadata_vars_missing_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Don't create metadata directory
        metadata = build_metadata_vars(Path(tmpdir))

        # Should have no metadata types and not raise an error
        assert not hasattr(metadata, "platform")
        assert not hasattr(metadata, "environment")
