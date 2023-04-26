from unittest import mock

import pytest
import requests
from brownie import accounts
from telliot_core.apps.core import TelliotCore
from web3 import Web3

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.feeds.xdai_usd_feed import xdai_usd_median_feed
from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.queries.query_catalog import query_catalog
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import get_native_token_feed
from telliot_feeds.utils.reporter_utils import has_native_token_funds
from telliot_feeds.utils.reporter_utils import is_online
from telliot_feeds.utils.reporter_utils import reporter_sync_schedule
from telliot_feeds.utils.reporter_utils import suggest_random_feed
from telliot_feeds.utils.reporter_utils import tellor_suggested_report


logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_suggested_report(tellor_360):
    contracts, _ = tellor_360
    qtag = await tellor_suggested_report(contracts.oracle)

    assert isinstance(qtag, str)
    entries = query_catalog.find(tag=qtag)
    assert len(entries) == 1
    catalog_entry = entries[0]
    q = catalog_entry.query
    assert isinstance(q, OracleQuery)


def test_reporter_sync_schedule_list():
    """Test reporter_sync_schedule list"""
    lis = reporter_sync_schedule
    assert len(lis) > 4
    assert "eth-usd-spot" in lis


@pytest.mark.asyncio
async def test_has_native_token_funds(mumbai_test_cfg, caplog):
    """Test has_native_token_funds"""

    def fake_alert(msg):
        logger.warning("bingo" + msg)

    def fail_balance_read(*args, **kwargs):
        raise Exception("bango")

    async with TelliotCore(config=mumbai_test_cfg) as core:
        account = core.get_account()
        addr = Web3.toChecksumAddress(account.address)
        endpoint = core.get_endpoint()
        endpoint.connect()

        # Test insufficient funds
        has_funds = has_native_token_funds(account=addr, web3=endpoint.web3, alert=fake_alert, min_balance=1e18)
        assert has_funds is False
        assert "bingo" in caplog.text
        assert "insufficient native token funds" in caplog.text.lower()

        # Fund account
        accounts[0].transfer(addr, "2 ether")

        # Test with funds
        has_funds = has_native_token_funds(account=addr, web3=endpoint.web3)
        assert has_funds is True

        # Test fail contract read
        with mock.patch("web3.eth.Eth.get_balance", side_effect=fail_balance_read):
            has_funds = has_native_token_funds(account=addr, web3=endpoint.web3, alert=fake_alert)
            assert has_funds is False
            assert "bango" in caplog.text
            assert f"Error fetching native token balance for {addr}" in caplog.text


def test_get_native_token_feed():
    """Test get_native_token_feed"""
    f = get_native_token_feed(1)
    assert f == eth_usd_median_feed

    f = get_native_token_feed(137)
    assert f == matic_usd_median_feed

    f = get_native_token_feed(10200)
    assert f == xdai_usd_median_feed

    with pytest.raises(ValueError):
        _ = get_native_token_feed(0)


@pytest.mark.asyncio
async def test_checking_if_online(caplog):
    """test telliot check for internet connection"""

    online = await is_online()
    assert isinstance(online, bool)

    with mock.patch("requests.get", side_effect=requests.exceptions.ConnectionError("test message")):

        online = await is_online()
        assert not online
        assert "Unable to connect to internet" in caplog.text
        assert "ConnectionError" in caplog.text

    with mock.patch("requests.get", side_effect=requests.exceptions.Timeout("test message")):

        online = await is_online()
        assert not online
        assert "Unable to connect to internet" in caplog.text
        assert "Timeout" in caplog.text


def test_suggest_random_feed():
    """Test suggest_random_feed"""
    feed = suggest_random_feed()

    assert isinstance(feed, DataFeed)
    assert feed in list(CATALOG_FEEDS.values())
