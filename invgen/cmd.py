import typer
from pathlib import Path
import shutil
import os

from invgen.logging import init_logger, logger
from invgen.hosts import generate_hosts, get_all_host_files
from invgen.inventory import inventory_app
from invgen.templates import render_template
from invgen.watcher import watch_for_changes

app = typer.Typer()
app_new = typer.Typer()
app_validate = typer.Typer()
app.add_typer(inventory_app, name="inventory")
app.add_typer(app_new, name="new")
app.add_typer(app_validate, name="validate")


@app.command()
def generate(
    source: Path = typer.Option(
        Path().cwd(), "-s", "--source", envvar="INVGEN_SOURCE", help="Source directory"
    ),
    verbose: bool = False,
    debug: bool = False,
    watch: bool = typer.Option(False, "-w", "--watch", help="Watch for changes"),
    clean: bool = typer.Option(False, "-c", "--clean", help="Clean generated directory before generating"),
):
    if verbose:
        init_logger("INFO")
    elif debug:
        init_logger("DEBUG")
    else:
        init_logger()

    if clean:
        generated_dir = source.joinpath("generated/")
        if generated_dir.exists():
            typer.echo(f"=> Cleaning {generated_dir}")
            shutil.rmtree(generated_dir)
            os.makedirs(generated_dir)

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


@app_new.command(name="metadata")
def new_metadata(
    metadata_type: str = typer.Option(..., help="Type of metadata (e.g., tags, platform)"),
    name: str = typer.Option(..., help="Name of the metadata file"),
    source: Path = typer.Option(
        Path().cwd(),
        "-s",
        "--source",
        envvar="INVGEN_SOURCE",
        help="Source directory",
    ),
    template: Path = typer.Option(
        None,
        "-t",
        "--template",
        help="Path to metadata template",
    ),
    options: str = typer.Option(
        "",
        "-o",
        "--options",
        help="Additional options as key=value pairs, separated by spaces",
    ),
):
    metadata_dir = source.joinpath(f"metadata/{metadata_type}")
    metadata_dir.mkdir(parents=True, exist_ok=True)

    output_path = metadata_dir.joinpath(f"{name}.yaml")

    if output_path.exists():
        typer.echo(typer.style(f"=> Error: Metadata file {output_path} already exists", fg=typer.colors.RED))
        raise typer.Exit(1)

    typer.echo(f"=> Creating new metadata {metadata_type}/{name}")

    if template:
        kwargs = {"name": name, "type": metadata_type}
        if options:
            for option in options.split(" "):
                key, value = option.split("=")
                kwargs[key.strip()] = value.strip()

        rendered = render_template(template, **kwargs)
        with open(output_path, "w") as f:
            f.write(rendered)
    else:
        # Create an empty metadata file
        with open(output_path, "w") as f:
            f.write("# Metadata file for {0}/{1}\n".format(metadata_type, name))
            f.write("---\n")

    typer.echo(f"=> Done! Created new metadata in {output_path}")


@app_validate.command(name="hosts")
def validate_hosts(
    source: Path = typer.Option(
        Path().cwd(), "-s", "--source", envvar="INVGEN_SOURCE", help="Source directory"
    ),
):
    """Validate all host files in the inventory"""
    init_logger("INFO")

    host_files = get_all_host_files(source)
    errors = []

    typer.echo(f"=> Validating {len(host_files)} host files")

    for host_file in host_files:
        try:
            from invgen.files import load_yaml_cached
            host_data = load_yaml_cached(host_file)

            # Check for required fields
            if "metadata" not in host_data:
                errors.append(f"{host_file.name}: Missing 'metadata' section")
            elif not isinstance(host_data["metadata"], dict):
                errors.append(f"{host_file.name}: 'metadata' must be a dictionary")

        except Exception as e:
            errors.append(f"{host_file.name}: {str(e)}")

    if errors:
        typer.echo(typer.style("=> Validation failed with errors:", fg=typer.colors.RED))
        for error in errors:
            typer.echo(typer.style(f"  - {error}", fg=typer.colors.RED))
        raise typer.Exit(1)
    else:
        typer.echo(typer.style("=> All host files are valid", fg=typer.colors.GREEN))
