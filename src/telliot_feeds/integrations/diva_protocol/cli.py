import click

from telliot_feeds.integrations.diva_protocol.utils import get_reported_pools
from telliot_feeds.integrations.diva_protocol.utils import update_reported_pools


@click.group()
def diva() -> None:
    """Commands for Diva Protocol integration."""
    pass


@diva.group()
def cache() -> None:
    """Commands for interacting with reported/settled pools cache (pickle file)."""
    pass


@cache.command()
def view() -> None:
    """View reported/settled pools cache."""
    cache = get_reported_pools()
    if cache:
        click.echo("Reported/Settled Pools Cache:")
    else:
        click.echo("Reported/Settled Pools Cache is empty")
        return
    for pool_id in cache:
        click.echo(f"Pool ID: {pool_id}")
        expiry, status = cache[pool_id]
        click.echo(f"\tExpiry: {expiry}")
        click.echo(f"\tSettle status: {status}")


@cache.command()
def clear() -> None:
    """Clear reported/settled pools cache.

    Creates and saves an empty dict as a pickle file in the telliot default dir."""
    update_reported_pools({})
    click.echo("Cleared reported/settled pools cache")
