# Dynamic Ansible Inventory

This is a dynamic inventory script for Ansible that reads the inventory from a
directory. A list of hosts is managed by the user. Each host has metadata that is used to gather variables.

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

The `hosts` directory contains host files that define the hosts.

The `generated` directory contains generated host files that are created by the script and used as an inventory.

The `metadata` directory contains metadata files that can be used to give hosts variables.
To use the metadata, the host file must have a `metadata` key that contains a list of metadata files.

```yaml
metadata:
  tags:
    - tag1
  platform: platform1
  my_custom_metadata: my_custom_metadata1
```

Under [example/](./example/) you can find an example of how to build an inventory.

Jinja2 can be used inside of variables, because it is parsed by Ansible at runtime.

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

## Usage

Install with `pip install -U invgen` or `uv tool install -U invgen`.

### Generate Inventory

```bash
# set the environment variable INVGEN_SOURCE to the path of the inventory directory
export INVGEN_SOURCE="$PWD/example/"

# generate the host files
invgen generate --verbose

# regenerate on file change
invgen generate --verbose --watch
```

### Ansible

```bash
# set the environment variable INVGEN_SOURCE to the path of the inventory directory
export INVGEN_SOURCE="$PWD/example/"

# run playbook with the inventory
ansible-playbook -i $(which invgen-ansible) playbook.yaml

# explore the inventory
❯ ansible-inventory -i $(which invgen-ansible) --graph
 [ERROR]: 2024-11-23 19:22:29,537 - INFO - inventory - Generating inventory from /home/fwrage/dev/invgen/example
[WARNING]: Invalid characters were found in group names but not replaced, use -vvvv to see details
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

### Templates

It is possible to use Jinja2 templates to generate host files.

```yaml
---
metadata:
    platform: {{ platform }}
    provider: {{ provider }}
    services: {{ services }}

ansible_host: {{ name }}
```

```bash
## Host
invgen new host -t example/templates/host.yaml -d example/hosts --name "ap02.test.local" -o "platform=raspberry-pi-4 provider=self-hosted services=pihole,dnsmasq"
```
