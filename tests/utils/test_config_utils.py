import os
import shutil
from pathlib import Path
from unittest import mock

import pytest
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import EndpointList
from telliot_core.model.endpoints import RPCEndpoint

from telliot_feeds.utils.cfg import check_accounts
from telliot_feeds.utils.cfg import check_endpoint
from telliot_feeds.utils.cfg import prompt_for_endpoint
from telliot_feeds.utils.cfg import setup_account
from telliot_feeds.utils.cfg import setup_config


@pytest.fixture
def mock_config():

    ep = EndpointList()

    cfg = TelliotConfig()
    mock_config_dir = os.path.join(os.getcwd(), ".mock_config")

    mock_path = Path.home() / mock_config_dir
    mock_path = mock_path.resolve().absolute()

    if not os.path.isdir(mock_config_dir):
        os.makedirs(mock_config_dir)

    cfg.config_dir = mock_path
    cfg._ep_config_file.config_dir = mock_path
    cfg._ep_config_file.save_config(ep)

    yield cfg  # test happens here

    shutil.rmtree(os.path.join(os.getcwd(), ".mock_config"))


@pytest.fixture
def mock_account():
    # since there is no remove() func for ChainedAccounts
    # we will add an account if the account does not exist in our keyfile
    try:
        fake_private_key = "ff27eb0c5059fc99f9d7b48931d135b20f1293db8d0f4fec4ecf5131fb40f1f5"  # https://vanity-eth.tk/
        return ChainedAccount.add("_mock_goerli_acct", 5, fake_private_key, "password")
    except Exception:
        return find_accounts(chain_id=5, name="_mock_goerli_acct")[0]


def test_update_all_configs(mock_config, mock_account):
    """test updating chain id, endpoint, and account"""

    cfg = mock_config
    print("mock config chain id:", cfg.main.chain_id)
    mock_acct = mock_account
    print("mock account:", mock_acct)

    # confirmations
    update_settings = True
    update_chain_id = True
    use_endpoint = False

    # prompts
    new_chain_id = 5

    # other mocks
    mock_endpoint = RPCEndpoint(5, "goerli", "infura", "myinfuraurl...", "etherscan.com")

    with (
        mock.patch("click.confirm", side_effect=[update_settings, update_chain_id, use_endpoint]),
        mock.patch("click.prompt", side_effect=[new_chain_id]),
        mock.patch("telliot_feeds.utils.cfg.setup_endpoint", side_effect=[mock_endpoint]),
        mock.patch("telliot_feeds.utils.cfg.setup_account", return_value=mock_acct),
    ):
        file_before = cfg._ep_config_file.get_config()
        assert mock_endpoint not in file_before.endpoints
        cfg, account = setup_config(cfg=cfg, account_name="_mock_goerli_acct")
        assert cfg.main.chain_id == new_chain_id
        assert check_endpoint(cfg) == mock_endpoint
        assert "_mock_goerli_acct" in account.name
        file_after = cfg._ep_config_file.get_config()
        assert mock_endpoint in file_after.endpoints
        # assert len(file_after.endpoints) > len(file_before.endpoints)


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


@pytest.mark.skip("unsupported by gh actions ubuntu")
def test_setup_account(mock_config):
    """Test accepting first account, then test adding an account"""

    chain_id = 5

    first_index = 0
    last_index = len(find_accounts(chain_id=chain_id))

    with (mock.patch("simple_term_menu.TerminalMenu.show", side_effect=[first_index]),):
        accounts = find_accounts(chain_id=chain_id)
        selected_acc = setup_account(chain_id)

        assert selected_acc.name == accounts[0].name

    with (
        mock.patch("simple_term_menu.TerminalMenu.show", side_effect=[last_index]),
        mock.patch("telliot_feeds.utils.cfg.prompt_for_account", side_effect=[mock_account]),
    ):
        cfg = mock_config
        cfg.main.chain_id = 5
        selected_acc = setup_account(cfg.main.chain_id)

        assert "_mock_goerli_acct" in [a.name for a in check_accounts(cfg, "_mock_goerli_acct")]


def test_not_updating_settings(mock_config):
    """test declining to update settings on click.confirm prompt"""

    cfg = mock_config

    # confirmations
    update_settings = False

    # other mocks
    mock_endpoint = RPCEndpoint(5, "goerli", "infura", "myinfuraurl...", "etherscan.com")

    with (
        mock.patch("click.confirm", side_effect=[update_settings]),
        mock.patch("telliot_feeds.utils.cfg.setup_endpoint", side_effect=[mock_endpoint]),
        mock.patch("telliot_feeds.utils.cfg.setup_account", return_value=mock_account()),
    ):
        file_before = cfg._ep_config_file.get_config()
        cfg, account = setup_config(cfg=cfg, account_name="_mock_goerli_acct")
        assert check_endpoint(cfg) != mock_endpoint
        assert "_mock_goerli_acct" in account.name
        file_after = cfg._ep_config_file.get_config()

        assert len(file_after.endpoints) == len(file_before.endpoints)


def test_continue_with_incomplete_settings(mock_config):
    """test declining to update settings when account and endpoints are unset"""
    cfg = mock_config
    print("cfg.main.chain_id", cfg.main.chain_id)

    # confirmations
    update_settings = False

    # other mocks
    mock_endpoint = RPCEndpoint(5, "goerli", "infura", "myinfuraurl...", "etherscan.com")

    with (
        mock.patch("click.confirm", side_effect=[update_settings]),
        mock.patch("telliot_feeds.utils.cfg.setup_endpoint", side_effect=[mock_endpoint]),
        mock.patch("telliot_feeds.utils.cfg.setup_account", return_value=mock_account()),
    ):
        file_before = cfg._ep_config_file.get_config()
        cfg, account = setup_config(cfg=cfg, account_name="_mock_goerli_acct2")
        assert check_endpoint(cfg) != mock_endpoint
        assert not account
        file_after = cfg._ep_config_file.get_config()

        assert len(file_after.endpoints) == len(file_before.endpoints)
