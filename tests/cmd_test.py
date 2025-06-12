import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from invgen.cmd import app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_inventory_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create basic directory structure
        os.makedirs(os.path.join(tmpdir, "hosts"))
        os.makedirs(os.path.join(tmpdir, "metadata"))
        os.makedirs(os.path.join(tmpdir, "generated"))

        # Create a simple host file
        with open(os.path.join(tmpdir, "hosts", "test-host.yaml"), "w") as f:
            f.write("""
metadata:
  platform: test-platform
  environment: test-env

ansible_host: 192.168.1.100
            """)

        # Create metadata files
        os.makedirs(os.path.join(tmpdir, "metadata", "platform"))
        with open(
            os.path.join(tmpdir, "metadata", "platform", "test-platform.yaml"), "w"
        ) as f:
            f.write("""
cpu_arch: x86_64
memory: 8GB
            """)

        os.makedirs(os.path.join(tmpdir, "metadata", "environment"))
        with open(
            os.path.join(tmpdir, "metadata", "environment", "test-env.yaml"), "w"
        ) as f:
            f.write("""
backup_enabled: true
            """)

        yield Path(tmpdir)


def test_generate_command(runner, temp_inventory_dir):
    result = runner.invoke(
        app, ["generate", "--source", str(temp_inventory_dir), "--verbose"]
    )

    assert result.exit_code == 0
    assert "Generating hosts" in result.stdout
    assert "Done! Generated hosts" in result.stdout

    # Check that the generated file exists
    generated_file = temp_inventory_dir / "generated" / "test-host.yaml"
    assert generated_file.exists()

    # Check content of generated file
    with open(generated_file) as f:
        content = f.read()
        assert "cpu_arch: x86_64" in content
        assert "backup_enabled: true" in content
        assert "ansible_host: 192.168.1.100" in content


def test_new_host_command(runner, temp_inventory_dir):
    # Create a template file
    template_dir = temp_inventory_dir / "templates"
    os.makedirs(template_dir)
    with open(template_dir / "host.yaml", "w") as f:
        f.write("""
metadata:
  platform: {{ platform }}
  environment: {{ environment }}

ansible_host: {{ name }}
        """)

    result = runner.invoke(
        app,
        [
            "new",
            "host",
            "--template",
            str(template_dir / "host.yaml"),
            "--destination",
            str(temp_inventory_dir / "hosts"),
            "--name",
            "new-test-host",
            "--options",
            "platform=test-platform environment=test-env",
        ],
    )

    assert result.exit_code == 0
    assert "Creating new host" in result.stdout
    assert "Done! Created new host" in result.stdout

    # Check that the new host file exists
    new_host_file = temp_inventory_dir / "hosts" / "new-test-host.yaml"
    assert new_host_file.exists()

    # Check content of new host file
    with open(new_host_file) as f:
        content = f.read()
        assert "platform: test-platform" in content
        assert "environment: test-env" in content
        assert "ansible_host: new-test-host" in content


@patch("invgen.cmd.watch_for_changes")
def test_generate_with_watch(mock_watch, runner, temp_inventory_dir):
    result = runner.invoke(
        app, ["generate", "--source", str(temp_inventory_dir), "--watch"]
    )

    assert result.exit_code == 0
    mock_watch.assert_called_once_with(temp_inventory_dir)


@patch("invgen.cmd.shutil.rmtree")
@patch("invgen.cmd.os.makedirs")
def test_generate_with_clean(mock_makedirs, mock_rmtree, runner, temp_inventory_dir):
    result = runner.invoke(
        app, ["generate", "--source", str(temp_inventory_dir), "--clean"]
    )

    assert result.exit_code == 0
    mock_rmtree.assert_called_once()
    mock_makedirs.assert_called_once()
