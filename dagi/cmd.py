import typer
from pathlib import Path

from dagi.logging import init_logger
from dagi.hosts import generate_hosts

app = typer.Typer()


@app.command()
def generate(
    source: Path = Path("data/"),
    verbose: bool = False,
    debug: bool = False,
    help="Generate host files",
):
    if verbose:
        init_logger("INFO")
    elif debug:
        init_logger("DEBUG")
    else:
        init_logger()

    print(source.absolute())
    generate_hosts(source)
