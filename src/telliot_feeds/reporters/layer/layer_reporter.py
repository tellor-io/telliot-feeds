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
from telliot_feeds.reporters.layer.client import LCDClient  # type: ignore[attr-defined]
from telliot_feeds.reporters.layer.msg_submit_value import MsgSubmitValue  # type: ignore[attr-defined]
from telliot_feeds.reporters.layer.msg_tip import MsgTip  # type: ignore[attr-defined]
from telliot_feeds.reporters.layer.raw_key import RawKey  # type: ignore[attr-defined]
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

        datafeed = feed_from_catalog_feeds(base64.b64decode(query)) if query else None

        return datafeed

    async def fetch_tx_info(self, response: Any) -> Optional[Dict[str, Any]]:
        for _ in range(10):
            try:
                tx_info = await self.client._get(f"/cosmos/tx/v1beta1/txs/{response.txhash}")
                return tx_info  # type: ignore[no-any-return]
            except Exception as e:
                if "tx not found" in str(e):
                    print("tx not found, retrying...")
                    await asyncio.sleep(1)
                    continue
                else:
                    # TODO: Handle other potential exceptions
                    raise e
        return None

    async def direct_submit_txn(self, datafeed: DataFeed[Any]) -> Tuple[Optional[Dict[str, Any]], ResponseStatus]:
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

    async def direct_tip_txn(self, datafeed: DataFeed[Any]) -> Tuple[Optional[Dict[str, Any]], ResponseStatus]:
        """Submit a direct tip transaction for a query"""
        print("SPUD STARTING direct_tip_txn")
        try:
            wallet = self.client.wallet(RawKey(self.account.local_account.key))
            tip_amount = Coin.from_str("1000loya")
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

    async def direct_tip_and_report_txn(
        self, datafeed: DataFeed[Any]
    ) -> Tuple[Optional[Dict[str, Any]], ResponseStatus]:
        """Submits the tip and the report in the same block"""
        print("SPUD STARTING direct_tip_and_report_txn")

        # Fetch and encode latest datapoint
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

        try:
            wallet = self.client.wallet(RawKey(self.account.local_account.key))

            # Tip message
            tip_amount = Coin.from_str("1000loya")
            tip_msg = MsgTip(
                tipper=wallet.key.acc_address,
                query_data=datafeed.query.query_data,
                amount=tip_amount.to_data(),
            )

            # Report message
            report_msg = MsgSubmitValue(
                creator=wallet.key.acc_address,
                query_data=datafeed.query.query_data,
                value=value.hex(),
            )

            # Single tx with both messages
            options = CreateTxOptions(
                msgs=[tip_msg, report_msg],
                gas=self.gas,
            )
            print(f"Combined options: {options}")

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
            if datafeed is None:
                return None, error_status("No datafeed available", log=logger.error)
            txn_info, status = await self.direct_tip_and_report_txn(datafeed)
            if txn_info is None or not status.ok:
                return None, error_status("Tip+Report transaction failed", e=status.e, log=logger.error)

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

    async def report(self) -> None:
        """Submit values to Tellor oracles on an interval."""
        while True:
            if await self.is_online():
                _, _ = await self.report_once()
            else:
                logger.warning("Unable to connect to the internet!")

            logger.info(f"Sleeping for {self.wait_period} seconds")
            await asyncio.sleep(self.wait_period)
