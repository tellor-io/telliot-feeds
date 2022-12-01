import click
import yaml
from telliot_core.apps.telliot_config import TelliotConfig


@click.group()
def config() -> None:
    """Manage Telliot configuration."""
    pass


@config.command()
def init() -> None:
    """Create initial configuration files."""
    _ = TelliotConfig()


@config.command()
def show() -> None:
    """Show current configuration."""
    cfg = TelliotConfig()
    state = cfg.get_state()

    print(yaml.dump(state, sort_keys=False))
