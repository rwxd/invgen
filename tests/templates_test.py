import tempfile
from pathlib import Path

import pytest
import jinja2

from invgen.templates import render_template


def test_render_template():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a template file
        template_path = Path(tmpdir) / "test_template.yaml"
        with open(template_path, "w") as f:
            f.write("""
name: {{ name }}
platform: {{ platform }}
{% if optional is defined %}
optional: {{ optional }}
{% endif %}
            """)

        # Render template with required variables
        result = render_template(
            template_path, name="test-host", platform="test-platform"
        )

        assert "name: test-host" in result
        assert "platform: test-platform" in result
        assert "optional:" not in result

        # Render template with optional variable
        result = render_template(
            template_path,
            name="test-host",
            platform="test-platform",
            optional="test-optional",
        )

        assert "name: test-host" in result
        assert "platform: test-platform" in result
        assert "optional: test-optional" in result


def test_render_template_undefined_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a template file
        template_path = Path(tmpdir) / "test_template.yaml"
        with open(template_path, "w") as f:
            f.write("""
name: {{ name }}
platform: {{ platform }}
required: {{ required }}
            """)

        # Should raise an error when a required variable is missing
        with pytest.raises(jinja2.exceptions.UndefinedError):
            render_template(template_path, name="test-host", platform="test-platform")

        # Should not raise an error when undefined_error is False
        result = render_template(
            template_path,
            undefined_error=False,
            name="test-host",
            platform="test-platform",
        )

        assert "name: test-host" in result
        assert "platform: test-platform" in result
