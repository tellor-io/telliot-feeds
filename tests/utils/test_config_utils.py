from unittest import mock

from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from simple_term_menu import TerminalMenu
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feeds.utils.cfg import check_accounts
from telliot_feeds.utils.cfg import check_endpoint
from telliot_feeds.utils.cfg import prompt_for_endpoint
from telliot_feeds.utils.cfg import setup_account
from telliot_feeds.utils.cfg import setup_config


def mock_account():
    # since there is no remove() func for ChainedAccounts
    # we will add an account if the account does not exist in our keyfile
    try:
        fake_private_key = "ff27eb0c5059fc99f9d7b48931d135b20f1293db8d0f4fec4ecf5131fb40f1f5"  # https://vanity-eth.tk/
        return ChainedAccount.add("mock-account", 4, fake_private_key, "password")
    except Exception:
        return find_accounts(chain_id=4, name="mock-account")[0]


def test_update_all_configs():
    """test updating chain id, endpoint, and account"""

    cfg = TelliotConfig()

    # confirmations
    update_chain_id = True
    use_endpoint = True

    # prompts
    new_chain_id = 4

    # other mocks
    mock_endpoint = RPCEndpoint(4, "rinkeby", "infura", "myinfuraurl...", "etherscan.com")

    with (
        mock.patch("click.confirm", side_effect=[update_chain_id, use_endpoint]),
        mock.patch("click.prompt", side_effect=[new_chain_id]),
        mock.patch("telliot_feeds.utils.cfg.setup_endpoint", side_effect=[mock_endpoint]),
        mock.patch("telliot_feeds.utils.cfg.setup_account", return_value=mock_account()),
    ):

        cfg, account = setup_config(cfg=cfg)
        print("account ", account)
        assert cfg.main.chain_id == new_chain_id
        assert check_endpoint(cfg) == mock_endpoint
        assert "mock-account" in account.name


def test_prompt_for_endpoint():
    """Test endpoint prompts with click that build a new RPCEndpoint"""

    network_name = "mainnet"
    provider = "infura"
    rpc_url = "infura.com..."
    explorer_url = "etherscan.io"

    with (mock.patch("click.prompt", side_effect=[network_name, provider, rpc_url, explorer_url])):
        chain_id = 1

        endpt = prompt_for_endpoint(chain_id)

        assert endpt.chain_id == chain_id
        assert endpt.provider == provider
        assert endpt.url == rpc_url
        assert endpt.explorer == explorer_url


def test_setup_account():
    """Test accepting first account, then test adding an account"""

    first_index = 0
    last_index = -1

    with (mock.patch.object(TerminalMenu, "show", side_effect=[first_index]),):
        chain_id = 4
        accounts = find_accounts(chain_id=chain_id)
        selected_acc = setup_account(chain_id)

        assert selected_acc.name == accounts[0].name

    with (
        mock.patch.object(TerminalMenu, "show", side_effect=[last_index]),
        mock.patch("telliot_feeds.utils.cfg.prompt_for_account", side_effect=[mock_account]),
    ):
        cfg = TelliotConfig()
        cfg.main.chain_id = 4
        selected_acc = setup_account(cfg.main.chain_id)

        assert "mock-account" in [a.name for a in check_accounts(cfg)]
