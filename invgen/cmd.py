import typer
from pathlib import Path

from invgen.logging import init_logger, logger
from invgen.hosts import generate_hosts

app = typer.Typer()


@app.command()
def generate(
    source: Path = typer.Option(
        Path("data/"), envvar="DAGI_SOURCE", help="Source directory"
    ),
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

    logger.info(f"Generating host files from {source}")
    generate_hosts(source)
