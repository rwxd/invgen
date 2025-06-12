import json

import pytest
from invgen.inventory import AnsibleInventory
from invgen.hosts import GeneratedHost


@pytest.fixture
def sample_hosts():
    return [
        GeneratedHost(
            name="host1",
            vars={
                "ansible_host": "192.168.1.10",
                "metadata": {
                    "platform": "raspberry-pi-4",
                    "environment": "production",
                    "tags": ["web", "database"],
                },
            },
        ),
        GeneratedHost(
            name="host2",
            vars={
                "ansible_host": "192.168.1.11",
                "metadata": {
                    "platform": "raspberry-pi-4",
                    "environment": "staging",
                    "tags": ["web"],
                },
            },
        ),
        GeneratedHost(
            name="host3",
            vars={
                "ansible_host": "192.168.1.12",
                "metadata": {
                    "platform": "x86-server",
                    "environment": "production",
                },
            },
        ),
    ]


def test_build_groups(sample_hosts):
    inventory = AnsibleInventory(sample_hosts)
    groups = inventory._build_groups()

    # Convert to dict for easier testing
    group_dict = {group.name: group.hosts for group in groups}

    assert "platform_raspberry-pi-4" in group_dict
    assert "platform_x86-server" in group_dict
    assert "environment_production" in group_dict
    assert "environment_staging" in group_dict
    assert "tags_web" in group_dict
    assert "tags_database" in group_dict

    assert set(group_dict["platform_raspberry-pi-4"]) == {"host1", "host2"}
    assert set(group_dict["environment_production"]) == {"host1", "host3"}
    assert set(group_dict["tags_web"]) == {"host1", "host2"}
    assert set(group_dict["tags_database"]) == {"host1"}


def test_build_hostvars(sample_hosts):
    inventory = AnsibleInventory(sample_hosts)
    hostvars = inventory._build_hostvars()

    assert "host1" in hostvars
    assert "host2" in hostvars
    assert "host3" in hostvars

    assert hostvars["host1"]["ansible_host"] == "192.168.1.10"
    assert hostvars["host2"]["ansible_host"] == "192.168.1.11"
    assert hostvars["host3"]["ansible_host"] == "192.168.1.12"


def test_build_inventory(sample_hosts):
    inventory = AnsibleInventory(sample_hosts)
    result = inventory.build()

    assert "_meta" in result
    assert "hostvars" in result["_meta"]
    assert "all" in result
    assert "hosts" in result["all"]

    # Check that all hosts are in the all group
    assert set(result["all"]["hosts"]) == {"host1", "host2", "host3"}

    # Check that specific groups exist
    assert "platform_raspberry-pi-4" in result
    assert "environment_production" in result
    assert "tags_web" in result


def test_render_inventory(sample_hosts):
    inventory = AnsibleInventory(sample_hosts)

    # Test without pretty printing
    result = inventory.render()
    parsed = json.loads(result)
    assert "_meta" in parsed

    # Test with pretty printing
    pretty_result = inventory.render(pretty=True)
    assert "  " in pretty_result  # Should have indentation
    parsed_pretty = json.loads(pretty_result)
    assert parsed == parsed_pretty


def test_build_host(sample_hosts):
    inventory = AnsibleInventory(sample_hosts)

    # Test existing host
    host1_vars = inventory.build_host("host1")
    assert host1_vars["ansible_host"] == "192.168.1.10"

    # Test non-existent host
    empty_vars = inventory.build_host("non_existent_host")
    assert empty_vars == {}


def test_render_host(sample_hosts):
    inventory = AnsibleInventory(sample_hosts)

    # Test without pretty printing
    result = inventory.render_host("host1")
    parsed = json.loads(result)
    assert parsed["ansible_host"] == "192.168.1.10"

    # Test with pretty printing
    pretty_result = inventory.render_host("host1", pretty=True)
    assert "  " in pretty_result  # Should have indentation
