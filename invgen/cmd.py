import typer
from pathlib import Path

from invgen.logging import init_logger
from invgen.hosts import generate_hosts
from invgen.inventory import inventory_app
from invgen.templates import render_template
from invgen.watcher import watch_for_changes

app = typer.Typer()
app_new = typer.Typer()
app.add_typer(inventory_app, name="inventory")
app.add_typer(app_new, name="new")


@app.command()
def generate(
    source: Path = typer.Option(
        Path().cwd(), "-s", "--source", envvar="INVGEN_SOURCE", help="Source directory"
    ),
    verbose: bool = False,
    debug: bool = False,
    watch: bool = typer.Option(False, "-w", "--watch", help="Watch for changes"),
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

    if watch:
        watch_for_changes(source)


@app_new.command(name="host")
def new_host(
    destination: Path = typer.Option(
        Path().cwd() / "hosts/",
        "-d",
        "--destination",
        envvar="INVGEN_DESTINATION",
        help="Destination directory",
    ),
    template: Path = typer.Option(
        Path("templates/host.yaml"),
        "-t",
        "--template",
        envvar="INVGEN_HOST_TEMPLATE",
        help="Path to host template",
    ),
    name: str = typer.Option(..., help="Name of the new host"),
    options: str = typer.Option(
        "",
        "-o",
        "--options",
        help="Additional options as key=value pairs, separated by spaces. "
        + "Can be a list seperated by commas.",
    ),
    ignore_errors: bool = typer.Option(
        False, "--ignore-errors", help="Ignore errors in the template"
    ),
):
    typer.echo(f"=> Creating new host {name} from {template}")

    kwargs: dict[str, str | list] = {"name": name}
    if options:
        for option in options.split(" "):
            key, value = option.split("=")
            if "," in value:
                kwargs[key.strip()] = value.split(",")
            else:
                kwargs[key.strip()] = value.strip()
    else:
        typer.echo(typer.style("=> No options provided.", fg=typer.colors.YELLOW))

    rendered = render_template(template, undefined_error=not ignore_errors, **kwargs)
    with open(destination / f"{name}.yaml", "w") as f:
        f.write(rendered)

    typer.echo(f"=> Done! Created new host in {destination}/{name}.yaml")
