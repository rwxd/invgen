import typer
from pathlib import Path

from invgen.logging import init_logger
from invgen.hosts import generate_hosts
from invgen.inventory import inventory_app

app = typer.Typer()
app.add_typer(inventory_app, name="inventory")


@app.command()
def generate(
    source: Path = typer.Option(
        Path().cwd(), envvar="INVGEN_SOURCE", help="Source directory"
    ),
    verbose: bool = False,
    debug: bool = False,
):
    if verbose:
        init_logger("INFO")
    elif debug:
        init_logger("DEBUG")
    else:
        init_logger()

    typer.echo(f"=> Generating hosts from {source}/hosts/")
    generate_hosts(source)
    typer.echo(f"=> Done! Generated hosts in {source}/generated/")
