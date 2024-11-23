from invgen.files import save_yaml, load_yaml
from tempfile import TemporaryFile


def test_ansible_yaml_tag():
    input = """password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  336366
"""

    with TemporaryFile(mode="w+") as f:
        f.write(input)
        f.seek(0)

        assert load_yaml(f)["password"] == "$ANSIBLE_VAULT;1.1;AES256\n336366\n"
        f.seek(0)

        with TemporaryFile(mode="w+") as f2:
            save_yaml(f2, load_yaml(f))
            f2.seek(0)
            assert f2.read() == input
