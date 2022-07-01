import click
from telliot_core.apps.core import TelliotCore
from telliot_core.cli.utils import cli_core


DIVA_PROTOCOL_CHAINS = (137, 80001, 3)


def reporter_cli_core(ctx: click.Context) -> TelliotCore:
    """Get telliot core configured in reporter CLI context"""
    # Delegate to main cli core getter
    # (handles ACCOUNT_NAME, CHAIN_ID, and TEST_CONFIG)
    core = cli_core(ctx)

    # Ensure chain id compatible with flashbots relay
    if ctx.obj["SIGNATURE_ACCOUNT_NAME"] is not None:
        # Only supports mainnet
        assert core.config.main.chain_id == 1

    assert core.config

    return core


def valid_diva_chain(chain_id: int) -> bool:
    """Ensure given chain ID supports reporting Diva Protocol data."""
    if chain_id not in DIVA_PROTOCOL_CHAINS:
        print(
            f"Current chain id ({chain_id}) not supported for reporting Diva Protocol data."
        )
        return False
    return True
