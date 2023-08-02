import pytest
from brownie import accounts
from telliot_core.apps.core import TelliotCore
from web3.datastructures import AttributeDict

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.numeric_api_response_query import NumericApiResponse
from telliot_feeds.reporters.tellor_360 import Tellor360Reporter
from telliot_feeds.sources.numeric_api_response import NumericApiResponseSource

url = "https://taylorswiftapi.herokuapp.com/get"
parseStr = "quote"
numeric_api_rsp_feed = DataFeed(
    source=NumericApiResponseSource(url=url, parseStr=parseStr),
    query=NumericApiResponse(url=url, parseStr=parseStr),
)


@pytest.mark.asyncio
async def test_api_reporter_submit_once(
    mumbai_test_cfg, mock_flex_contract, mock_autopay_contract, mock_token_contract
):
    """Test reporting a quote from T-Swizzle on Polygon Mumbai testnet."""
    async with TelliotCore(config=mumbai_test_cfg) as core:
        # get PubKey and PrivKey from config files
        account = core.get_account()

        flex = core.get_tellor360_contracts()
        flex.oracle.address = mock_flex_contract.address
        flex.autopay.address = mock_autopay_contract.address
        flex.token.address = mock_token_contract.address

        flex.oracle.connect()
        flex.token.connect()
        flex.autopay.connect()

        # mint token and send to reporter address
        mock_token_contract.faucet(account.address)

        # send eth from brownie address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")

        r = Tellor360Reporter(
            endpoint=core.endpoint,
            account=account,
            chain_id=80001,
            oracle=flex.oracle,
            token=flex.token,
            autopay=flex.autopay,
            transaction_type=0,
            datafeed=numeric_api_rsp_feed,
            max_fee_per_gas=100,
        )

        ORACLE_ADDRESSES = {mock_flex_contract.address}

        tx_receipt, status = await r.report_once()

        # Reporter submitted
        if tx_receipt is not None and status.ok:
            assert isinstance(tx_receipt, AttributeDict)
            assert tx_receipt.to in ORACLE_ADDRESSES
        # Reporter did not submit
        else:
            assert not tx_receipt
            assert not status.ok
            assert (
                ("Currently in reporter lock." in status.error)
                or ("Current address disputed" in status.error)
                or ("Unable to retrieve updated datafeed" in status.error)
            )
