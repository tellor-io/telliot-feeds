import click
import yaml
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.utils.cfg import setup_config


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


@click.option(
    "--account",
    "-a",
    "account_str",
    help="Name of account used for reporting, staking, etc. More info: run `telliot account --help`",
    required=False,
    nargs=1,
    type=str,
)
@config.command()
def update(
    account_str: str,
) -> None:
    """Update configuration."""
    _, _ = setup_config(None, account_str)
