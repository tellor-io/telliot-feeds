from unittest import mock
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import RPCEndpoint
from chained_accounts import ChainedAccount



from telliot_feeds.utils.cfg import setup_config, check_accounts, check_endpoint


def test_config_update_chain_id():
    """test updating chain id to chain id with known endpoint"""

    cfg = TelliotConfig()

    #confirmations
    update_chain_id = True
    use_endpoint = True

    #prompts
    new_chain_id = 1

    #other mocks
    mock_endpoint = RPCEndpoint(1, "mainnet", "infura", "myinfuraurl...", "etherscan.io")
    mock_account = ChainedAccount("mock-account")


    with (
        mock.patch("click.confirm", side_effect=[update_chain_id, use_endpoint]),
        mock.patch("click.prompt", side_effect=[new_chain_id]),
        mock.patch("telliot_feeds.utils.cfg.check_endpoint", return_value=mock_endpoint),
        mock.patch("telliot_feeds.utils.cfg.setup_account", return_value=mock_account)
        ):

        setup_config(cfg=cfg)

        assert cfg.main.chain_id == 1
        assert check_endpoint(cfg) == mock_endpoint
        assert check_accounts(cfg) == mock_account

def test_config_update_endpoint():
    """"""
