import asyncio
import base64
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from chained_accounts import ChainedAccount
from telliot_core.apps.core import RPCEndpoint
from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core.coins import Coin

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.queries.grip_dyno_challenge_query import EthDc2025Test2
from telliot_feeds.reporters.layer.client import LCDClient
from telliot_feeds.reporters.layer.msg_submit_value import MsgSubmitValue
from telliot_feeds.reporters.layer.msg_tip import MsgTip
from telliot_feeds.reporters.layer.raw_key import RawKey
from telliot_feeds.sources.manual.grip_dyno_manual_source import gripDynoManualSource
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.query_search_utils import feed_from_catalog_feeds
from telliot_feeds.utils.reporter_utils import is_online

logger = get_logger(__name__)


class LayerReporter:
    def __init__(
        self,
        wait_period: int,
        endpoint: RPCEndpoint,
        account: ChainedAccount,
        query_tag: str,
        datafeed: Optional[DataFeed[Any]] = None,
        ignore_tbr: bool = False,
        gas: str = "auto",
    ) -> None:
        """Initialize LayerReporter"""
        self.account = account
        self.datafeed = datafeed
        self.query_tag = query_tag
        # Get the datafeed from catalog if query_tag is provided
        self.datafeed = CATALOG_FEEDS[query_tag] if query_tag else None
        self.qtag_selected = query_tag is not None
        self.gas = gas
        self.wait_period = wait_period
        self.ignore_tbr = ignore_tbr
        self.client = LCDClient(url=endpoint.url, chain_id=endpoint.network)
        self.previously_reported_id: Optional[int] = None
        # needed for queries that have a long reporting window
        self.previously_reported_tipped_query: Dict[str, bool] = {"init": True}

    async def fetch_cycle_list_query(self) -> Tuple[Optional[str], ResponseStatus]:
        print("SPUD STARTING fetch_cycle_list_query")
        query_res = await self.client._get("/tellor-io/layer/oracle/current_cyclelist_query")
        querymeta = query_res.get("query_meta")
        if querymeta is None:
            return None, error_status("failed to get cycle list query", log=logger.error)
        current_id = querymeta["id"]
        # if already reported id, keep trying until you get a new id
        while current_id == self.previously_reported_id:
            query_res = await self.client._get("/tellor-io/layer/oracle/current_cyclelist_query")
            querymeta = query_res.get("query_meta")
            if querymeta is None:
                return None, error_status("failed to get cycle list query", log=logger.error)
            current_id = querymeta["id"]
        print("Query response:", query_res)
        self.previously_reported_id = current_id
        return querymeta["query_data"], ResponseStatus()

    async def fetch_tipped_query(self) -> Tuple[Optional[str], Optional[str]]:
        print("SPUD STARTING fetch_tipped_query")
        query_res = await self.client._get("/tellor-io/layer/oracle/tipped_queries")
        querymeta = query_res.get("queries")
        if len(querymeta) == 0:
            return None, None
        querydata = querymeta[0].get("query_data")
        if querydata in self.previously_reported_tipped_query:
            print("Already reported this query, skipping...")
            return None, None
        self.previously_reported_tipped_query[querydata] = True
        tip = querymeta[0].get("amount")
        return querydata, tip

    async def fetch_datafeed(self) -> Optional[DataFeed[Any]]:
        print("SPUD STARTING fetch_datafeed")
        query, tip = await self.fetch_tipped_query()
        print(f"\nTippedQuery: {query}\nTip: {tip}\n")
        if query is None:
            query, status = await self.fetch_cycle_list_query()
            if not status.ok:
                return None

        datafeed = feed_from_catalog_feeds(base64.b64decode(query))

        return datafeed

    async def fetch_tx_info(self, response) -> Optional[dict]:
        for _ in range(10):
            try:
                tx_info = await self.client._get(f"/cosmos/tx/v1beta1/txs/{response.txhash}")
                return tx_info
            except Exception as e:
                if "tx not found" in str(e):
                    print("tx not found, retrying...")
                    await asyncio.sleep(1)
                    continue
                else:
                    # TODO: Handle other potential exceptions
                    raise e
        return None

    async def direct_submit_txn(self, datafeed: DataFeed[Any]) -> Tuple[Optional[dict], ResponseStatus]:
        print("SPUD STARTING direct_submit_txn")
        await datafeed.source.fetch_new_datapoint()
        latest_data = datafeed.source.latest
        if latest_data[0] is None:
            msg = "Unable to retrieve updated datafeed value."
            return None, error_status(msg, log=logger.info)

        try:
            value = datafeed.query.value_type.encode(latest_data[0])
            logger.debug(f"Current query: {datafeed.query.descriptor}")
            logger.debug(f"Reporter Encoded value: {value.hex()}")
        except Exception as e:
            msg = f"Error encoding response value {latest_data[0]}"
            return None, error_status(msg, e=e, log=logger.error)

        wallet = self.client.wallet(RawKey(self.account.local_account.key))
        msg = MsgSubmitValue(
            creator=wallet.key.acc_address,
            query_data=datafeed.query.query_data,
            value=value.hex(),
        )
        print(f"submit value options: {msg}")
        options = CreateTxOptions(msgs=[msg], gas=self.gas)
        print(f"submit value options: {options}")
        try:
            tx = wallet.create_and_sign_tx(options)
            response = self.client.tx.broadcast_async(tx)
            return await self.fetch_tx_info(response), ResponseStatus()
        except Exception as e:
            msg = "Error submitting transaction"
            print(msg, e.__str__())
            return None, error_status(msg, e=e, log=logger.error)

    async def direct_tip_txn(self, datafeed: DataFeed[Any]) -> Tuple[Optional[dict], ResponseStatus]:
        """Submit a direct tip transaction for a query"""
        print("SPUD STARTING direct_tip_txn")
        try:
            wallet = self.client.wallet(RawKey(self.account.local_account.key))
            tip_amount = Coin.from_str("10000loya")
            msg = MsgTip(
                tipper=wallet.key.acc_address,
                query_data=datafeed.query.query_data,
                amount=tip_amount.to_data(),
            )

            print(f"Tip message: {msg}")

            # Get account sequence and number
            account_info = self.client.auth.account_info(wallet.key.acc_address)
            sequence = account_info.sequence
            account_number = account_info.account_number

            print(f"Account info - sequence: {sequence}, number: {account_number}")

            options = CreateTxOptions(
                msgs=[msg],
                gas=self.gas,
            )

            print(f"Tip options: {options}")

            tx = wallet.create_and_sign_tx(options)
            print(f"tx: {tx}")
            response = self.client.tx.broadcast_async(tx)
            print(f"response: {response}")
            return await self.fetch_tx_info(response), ResponseStatus()

        except Exception as e:
            msg = "Error creating/broadcasting transaction"
            logger.error(f"{msg}: {str(e)}")
            return None, error_status(msg, e=e, log=logger.error)

    async def report_once(
        self,
    ) -> Tuple[Optional[Any], ResponseStatus]:
        """Report query value once"""
        print("SPUD STARTING report_once")

        # Use the specified datafeed if query tag was provided
        if self.qtag_selected:
            print(f"query_tag_selected = {self.qtag_selected}")
            datafeed = self.datafeed

            tip_txn_info, tip_status = await self.direct_tip_txn(datafeed)
            if tip_txn_info is None or not tip_status.ok:
                return None, error_status("Tip transaction failed", e=tip_status.e, log=logger.error)

            tip_txn_response = tip_txn_info.get("tx_response")
            if tip_txn_response is None:
                return None, error_status("Failed to get tip transaction response", log=logger.error)

            tip_code = tip_txn_response.get("code")
            if tip_code == 0:
                tip_txn_hash = tip_txn_response.get("txhash")
                print(f"Txn hash: {tip_txn_hash}; Tip txn successful with status code {tip_code}")
            else:
                print(f"Transaction failed with status code {tip_code}")
                self.previously_reported_id = None

        else:
            # Otherwise fetch from chain
            datafeed = await self.fetch_datafeed()
            if not datafeed:
                return None, error_status(note="Unable to suggest datafeed", log=logger.info)

        txn_info, status = await self.direct_submit_txn(datafeed)
        if txn_info is None or not status.ok:
            return None, error_status("Failed to submit transaction", e=status.e, log=logger.error)

        txn_response = txn_info.get("tx_response")
        if txn_response is None:
            return None, error_status("Failed to get transaction response", log=logger.error)

        code = txn_response.get("code")
        if code == 0:
            txn_hash = txn_response.get("txhash")
            print(f"Txn hash: {txn_hash}; Transaction successful with status code {code}")
        else:
            print(f"Transaction failed with status code {code}")
            self.previously_reported_id = None

        return txn_info, ResponseStatus()

    async def is_online(self) -> bool:
        return await is_online()

    # change this to report cycle list if -qt flag is not there
    async def report(self) -> None:
        """Submit values to Tellor oracles on an interval."""
        print("SPUD STARTING report")
        while True:
            if await self.is_online():
                _, _ = await self.report_once()
            else:
                logger.warning("Unable to connect to the internet!")

            logger.info(f"Sleeping for {self.wait_period} seconds")
            await asyncio.sleep(self.wait_period)


async def test_direct_tip_txn():
    # Set up test inputs
    endpoint = RPCEndpoint(url="http://tellorlayer.com:1317", network="layertest-2")
    account = ChainedAccount("layerguy2")
    account.unlock("")

    query_tag = "grip-dyno-denver-2025"
    source = gripDynoManualSource()
    datafeed = DataFeed(
        query=EthDc2025Test2(challengeType="grip_strength_dynamometer"),
        source=source,
    )
    print(f"Datafeed: {datafeed}")

    reporter = LayerReporter(wait_period=10, endpoint=endpoint, account=account, query_tag=query_tag)

    txn_info, status = await reporter.direct_tip_txn(datafeed)

    print(f"Transaction info: {txn_info}")
    print(f"Status: {status}")


async def test_submit_value():
    # Set up test inputs
    endpoint = RPCEndpoint(url="http://tellorlayer.com:1317", network="layertest-2")
    account = ChainedAccount("layerguy2")
    account.unlock("")

    # Create mock datafeed
    datafeed = DataFeed(
        query=EthDc2025Test2(challengeType="grip_strength_dynamometer"),
        source=gripDynoManualSource(
            data_set=True, right_hand=99, left_hand=112, x_handle="asdf", github_username="qwer", hours_of_sleep=6
        ),
    )
    reporter = LayerReporter(wait_period=10, endpoint=endpoint, account=account, query_tag="grip-dyno-denver-2025")

    txn_info, status = await reporter.direct_submit_txn(datafeed)

    print(f"Transaction info: {txn_info}")
    print(f"Status: {status}")


if __name__ == "__main__":
    asyncio.run(test_direct_tip_txn())
    asyncio.run(test_submit_value())
