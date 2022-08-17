import pytest
import os

from telliot_feeds.funder.feed_funder import FeedFunder
from chained_accounts import find_accounts
from chained_accounts import ChainedAccount


@pytest.fixture(scope="module", autouse=True)
def fake_account():
    "Generate fake account if doesn't exist"
    chain_id = 123456789
    accounts = find_accounts(chain_id=chain_id)
    if not accounts:
        fake_key = "0x57fe7105302229455bcfd58a8b531b532d7a2bb3b50e1026afa455cd332bf706"
        ChainedAccount.add(f"fake-{chain_id}", [chain_id], fake_key, password="")
        accounts = find_accounts(chain_id=chain_id)[0]
    acc = accounts[0]
    acc.unlock("")
    return acc


def test_feed_funder(fake_account):
    "Test FeedFunder class"
    feed_funder = FeedFunder(account=fake_account)

    with pytest.riases(NotImplementedError):
        feed_funder.get_feeds_to_fund()

    with pytest.riases(NotImplementedError):
        feed_funder.fund_feeds()
    
    with pytest.riases(NotImplementedError):
        feed_funder.fund_feed()
    
    with pytest.riases(NotImplementedError):
        feed_funder.alert_funds_exhausted()
