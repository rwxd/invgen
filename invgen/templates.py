from jinja2 import Environment, FileSystemLoader
from pathlib import Path

import jinja2


def render_template(template_path: Path, undefined_error: bool = True, **kwargs) -> str:
    env = Environment(loader=FileSystemLoader(template_path.parent))
    if undefined_error:
        env.undefined = jinja2.StrictUndefined

    template = env.get_template(template_path.name)
    return template.render(**kwargs)
