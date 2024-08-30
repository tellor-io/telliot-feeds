# type: ignore
import asyncio
from typing import Any
from typing import Tuple
from typing import Optional

from chained_accounts import ChainedAccount

from telliot_core.utils.response import error_status
from telliot_core.utils.response import ResponseStatus

from telliot_feeds.feeds import DataFeed
from telliot_feeds.utils.log import get_logger
from telliot_feeds.utils.reporter_utils import is_online
from telliot_feeds.utils.query_search_utils import feed_from_catalog_feeds
from telliot_core.apps.core import RPCEndpoint
from telliot_feeds.reporters.layer.client import LCDClient
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from telliot_feeds.reporters.layer.msg_submit_value import MsgSubmitValue
from telliot_feeds.reporters.layer.raw_key import RawKey


logger = get_logger(__name__)


class LayerReporter:
    def __init__(
            self,
            endpoint: RPCEndpoint,
            account: ChainedAccount,
            wait_period: int,
            gas: str = "auto",
    ) -> None:
        self.account = account
        self.gas = gas
        self.wait_period = wait_period
        self.client = LCDClient(url=endpoint.url, chain_id=endpoint.network)

    async def fetch_cycle_list_query(self) -> Tuple[Optional[str], ResponseStatus]:
        query_res = await self.client._get("/tellor-io/layer/oracle/current_cyclelist_query")
        querydata = query_res.get("query_data")
        if querydata is None:
            return None, error_status("failed to get cycle list query", log=logger.error)
        return querydata, ResponseStatus()

    async def fetch_tipped_query(self) -> Tuple[Optional[str], Optional[str]]:
        query_res = await self.client._get("/tellor-io/layer/oracle/get_all_tipped_queries")
        querydata = query_res.get("query_data")
        tip = query_res.get("tip")
        return querydata, tip

    async def fetch_datafeed(self) -> Optional[DataFeed[Any]]:
        query, tip = await self.fetch_tipped_query()
        if query is None:
            query, status = await self.fetch_cycle_list_query()
            if not status.ok:
                return None

        datafeed = feed_from_catalog_feeds(bytes.fromhex(query))

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

    async def direct_submit_txn(self, datafeed: DataFeed[Any]) -> Optional[dict]:
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
            salt="",
        )
        options = CreateTxOptions(msgs=[msg], gas=self.gas)

        tx = wallet.create_and_sign_tx(options)
        response = self.client.tx.broadcast_sync(tx)
        return await self.fetch_tx_info(response)

    async def report_once(
        self,
    ) -> Tuple[Optional[Any], ResponseStatus]:
        """Report query value once"""
        datafeed = await self.fetch_datafeed()
        if not datafeed:
            msg = "Unable to suggest datafeed"
            return None, error_status(note=msg, log=logger.info)
        txn_info = await self.direct_submit_txn(datafeed)
        if txn_info is None:
            return None, error_status("Failed to submit transaction", log=logger.error)
        txn_response = txn_info.get("tx_response")
        if txn_response is None:
            return None, error_status("Failed to get transaction response", log=logger.error)
        code = txn_response.get("code")
        if code == 0:
            print("Transaction successful with status code 0")
            txn_hash = txn_response.get("txhash")
            print(f"Transaction hash: {txn_hash}")
        else:
            print("Transaction failed with status code", txn_info.code)
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
