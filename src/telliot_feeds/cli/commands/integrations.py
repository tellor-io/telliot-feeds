import click

from telliot_feeds.integrations.diva_protocol.cli import diva


@click.group()
def integrations() -> None:
    """Commands for Tellor Protocol integrations."""
    pass


integrations.add_command(diva)
