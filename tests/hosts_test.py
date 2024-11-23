from invgen.metadata import MetadataVars
from tempfile import NamedTemporaryFile
from invgen.hosts import generate_host_file
from pathlib import Path
import yaml


def test_generate_host_file():
    metadata = MetadataVars()
    items = {
        "customer": {
            "customer1": {"customer_var": "content"},
        },
        "environment": {
            "environment1": {"environment_var": "content"},
        },
        "groups": {
            "group1": {"group_var": "content"},
        },
        "location": {
            "location1": {"location_var": "content"},
        },
        "os": {
            "os1": {"os_var": "content"},
        },
        "services": {
            "service1": {"service_var": "content"},
        },
        "tags": {
            "tag1": {"tag_var": "content"},
        },
    }

    for key, value in items.items():
        metadata.add_metadata(key)
        for name, vars in value.items():
            metadata.set_vars(key, name, vars)

    host_vars = {
        "metadata": {
            "customer": "customer1",
            "os": "os1",
            "environment": "environment1",
            "location": "location1",
            "services": ["service1"],
            "groups": ["group1"],
            "tags": ["tag1"],
        },
        "host_var1": "content",
    }

    with NamedTemporaryFile(mode="w+") as f:
        yaml.safe_dump(host_vars, f)
        f.seek(0)

        generated = generate_host_file(Path(f.name), metadata)
        assert (
            generated
            == f"""
# customer/customer1.yaml
customer_var: content

# environment/environment1.yaml
environment_var: content

# groups/group1.yaml
group_var: content

# location/location1.yaml
location_var: content

# os/os1.yaml
os_var: content

# services/service1.yaml
service_var: content

# tags/tag1.yaml
tag_var: content

# hosts/{Path(f.name).stem}.yaml
host_var1: content
metadata:
  customer: customer1
  environment: environment1
  groups:
  - group1
  location: location1
  os: os1
  services:
  - service1
  tags:
  - tag1
"""
        )
