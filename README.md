# Dynamic Ansible Inventory

[![CI](https://github.com/rwxd/invgen/actions/workflows/ci.yml/badge.svg)](https://github.com/rwxd/invgen/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/rwxd/invgen/branch/main/graph/badge.svg)](https://codecov.io/gh/rwxd/invgen)

This is a dynamic inventory script for Ansible that reads the inventory from a
directory. A list of hosts is managed by the user. Each host has metadata that is used to gather variables.

## Directory Structure

The structure of the inventory directory is as follows:

```tree
hosts/
  host1.yaml
  host2.yaml
  host3.yaml
generated/
  host1.yaml
  host2.yaml
  host3.yaml
metadata/
  tags/
    tag1.yaml
    tag2.yaml
  platform/
    platform1.yaml
    platform2.yaml
  my_custom_metadata/
    my_custom_metadata1.yaml
    my_custom_metadata2.yaml
```

- The `hosts` directory contains host files that define the hosts.
- The `generated` directory contains generated host files that are created by the script and used as an inventory.
- The `metadata` directory contains metadata files that can be used to give hosts variables.

## Host Configuration

To use the metadata, the host file must have a `metadata` key that contains a list of metadata files:

```yaml
metadata:
  tags:
    - tag1
    - tag2
  platform: platform1
  my_custom_metadata: my_custom_metadata1
```

Under [example/](./example/) you can find an example of how to build an inventory.

## Variable Templating

Jinja2 can be used inside of variables, because it is parsed by Ansible at runtime:

```yaml
domain_name: example.com
hostname: ap01

ansible_host: "{{ hostname }}.{{ domain_name }}"

dns_servers:
  - 1.1.1.1
  - 8.8.8.8

network_interfaces:
  - name: eth0
    type: ethernet
    state: up
    ip: 192.168.1.100
    netmask: 255.255.255.0
    gateway: 192.168.1.1
    dns: "{{ dns_servers }}"
```

## Installation

Install with `pip install -U invgen` or `uv tool install -U invgen`.

## Usage

### Generate Inventory

```bash
# set the environment variable INVGEN_SOURCE to the path of the inventory directory
export INVGEN_SOURCE="$PWD/example/"

# generate the host files
invgen generate --verbose

# clean and regenerate host files
invgen generate --verbose --clean

# regenerate on file change
invgen generate --verbose --watch
```

### Create New Hosts and Metadata

```bash
# Create a new host from a template
invgen new host -t example/templates/host.yaml -d example/hosts --name "ap02.test.local" -o "platform=raspberry-pi-4 provider=self-hosted services=pihole,dnsmasq"

# Create a new metadata file
invgen new metadata --metadata-type platform --name "raspberry-pi-5" -s example/
```

### Validate Inventory

```bash
# Validate all host files
invgen validate hosts
```

### Use with Ansible

```bash
# set the environment variable INVGEN_SOURCE to the path of the inventory directory
export INVGEN_SOURCE="$PWD/example/"

# run playbook with the inventory
ansible-playbook -i $(which invgen-ansible) playbook.yaml

# explore the inventory
❯ ansible-inventory -i $(which invgen-ansible) --graph
@all:
  |--@ungrouped:
  |--@environment_production:
  |  |--ap01.test.local
  |--@provider_self-hosted:
  |  |--ap01.test.local
  |--@hardware_raspberry-pi-4:
  |  |--ap01.test.local
  |--@os_rhel-9:
  |  |--ap01.test.local
  |--@services_podman-rootless:
  |  |--ap01.test.local
  |--@tags_selinux-deactivated:
  |  |--ap01.test.local
```

## Variable Merging

When multiple metadata sources define the same variable:

- For scalar values (strings, numbers, booleans): The last processed value takes precedence
- For dictionaries and lists: Later values completely replace earlier values
- Host-specific values (defined directly in the host file) always take precedence over metadata values

The order of precedence (from lowest to highest):
1. Metadata files (processed in the order they appear in the host's metadata section)
2. Host-specific values (defined directly in the host file)

## Advanced Features

### Templating

You can use Jinja2 templates to generate host files:

```yaml
---
metadata:
    platform: {{ platform }}
    provider: {{ provider }}
    services: {{ services }}

ansible_host: {{ name }}
```

### Watching for Changes

The `--watch` flag allows the tool to automatically regenerate the inventory when files change:

```bash
invgen generate --verbose --watch
```
