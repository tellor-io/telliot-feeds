import pytest
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts

from telliot_feeds.funder.feed_funder import FeedFunder


@pytest.fixture(scope="module", autouse=True)
def fake_account():
    "Generate fake account if doesn't exist"
    chain_id = 123456789
    accounts = find_accounts(chain_id=chain_id)
    if not accounts:
        fake_key = "0x57fe7105302229455bcfd58a8b531b532d7a2bb3b50e1026afa455cd332bf706"
        ChainedAccount.add(f"fake-{chain_id}", [chain_id], fake_key, password="")
        accounts = find_accounts(chain_id=chain_id)
    acc = accounts[0]
    acc.unlock("")
    return acc


def test_feed_funder(fake_account):
    "Test FeedFunder class"
    # Can't instantiate abstract class FeedFunder with abstract methods
    # alert_funds_exhausted, fund_feeds, get_feeds_to_fund
    with pytest.raises(TypeError):
        _ = FeedFunder(account=fake_account)
