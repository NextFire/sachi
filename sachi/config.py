from importlib.metadata import metadata
from pathlib import Path

import rich
import tomlkit
import typer
from pydantic import BaseModel


def get_config_path() -> Path:
    if __package__ is None:
        raise ImportError("This module must be imported as a package")
    pkg_meta = metadata(__package__)
    app_dir = Path(typer.get_app_dir(pkg_meta["Name"]))
    app_dir.mkdir(parents=True, exist_ok=True)
    config_path = app_dir / "config.toml"
    return config_path


def read_config() -> tomlkit.TOMLDocument:
    config_path = get_config_path()
    if not config_path.exists():
        rich.print("[red]Missing config file, run `sachi config` to create one")
        raise typer.Exit(1)
    return tomlkit.parse(config_path.read_text(encoding="utf-8"))


def write_config(doc: tomlkit.TOMLDocument):
    config_path = get_config_path()
    config_path.write_text(tomlkit.dumps(doc), encoding="utf-8", newline="")


class BaseConfig(BaseModel):
    general: "GeneralConfig"
    series: "SeriesConfig"
    movie: "MovieConfig"


class GeneralConfig(BaseModel):
    dark: bool = True


class SeriesConfig(BaseModel):
    template: list[str]


class MovieConfig(BaseModel):
    template: list[str]
