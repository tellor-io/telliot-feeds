import click
from chained_accounts.cli import add as chained_accounts_add
from chained_accounts.cli import delete as chained_accounts_delete
from chained_accounts.cli import find as chained_accounts_find
from chained_accounts.cli import key as chained_accounts_key


@click.group()
def account() -> None:
    """Create, find, and manage accounts."""


account.add_command(chained_accounts_add)
account.add_command(chained_accounts_find)
account.add_command(chained_accounts_key)
account.add_command(chained_accounts_delete)
