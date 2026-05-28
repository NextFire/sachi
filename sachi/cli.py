from importlib.resources import files
from pathlib import Path
from typing import Annotated

import click
import rich
import typer

import sachi.resources
from sachi.app import SachiApp
from sachi.config import get_config_path

cli_app = typer.Typer()


@cli_app.command()
def config():
    config_path = get_config_path()
    if not config_path.exists():
        rich.print("No config file found, creating one")
        content = files(sachi.resources).joinpath("config.toml").read_bytes()
        config_path.write_bytes(content)
    rich.print(f'Editing "{config_path}"')
    click.edit(filename=config_path.as_posix())


@cli_app.command()
def rename(
    file_or_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=True,
            writable=True,
            readable=True,
        ),
    ],
):
    app = SachiApp(file_or_dir)
    app.run()
