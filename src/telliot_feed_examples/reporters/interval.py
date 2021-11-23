""" BTCUSD Price Reporter

Example of a subclassed Reporter.
"""
import asyncio
import time
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple

from telliot_core.contract.contract import Contract
from telliot_core.contract.gas import fetch_gas_price
from telliot_core.datafeed import DataFeed
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.response import ResponseStatus
from web3.datastructures import AttributeDict

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


class IntervalReporter:
    """Reports values from given datafeeds to a TellorX Oracle
    every 10 seconds."""

    def __init__(
        self,
        endpoint: RPCEndpoint,
        private_key: str,
        master: Contract,
        oracle: Contract,
        datafeeds: List[DataFeed[Any]],
    ) -> None:

        self.endpoint = endpoint
        self.private_key = private_key
        self.master = master
        self.oracle = oracle
        self.datafeeds = datafeeds

    async def report_once(
        self, retries: int = 0
    ) -> List[Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]]:
        """Submit value once"""
        status = ResponseStatus()
        gas_price_gwei = await fetch_gas_price()

        transaction_receipts: List[
            Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]
        ] = []

        user = self.endpoint.web3.eth.account.from_key(self.private_key).address
        logger.info(f"Reporting with account: {user}")
        is_staked, read_status = await self.master.read("getStakerInfo", _staker=user)

        if (not read_status.ok) or (is_staked is None):
            status.ok = False
            status.error = (
                "unable to read reporters staker status: " + read_status.error
            )  # error won't be none # noqa: E501
            status.e = read_status.e
            transaction_receipts.append((None, status))

        else:

            last_timestamp, read_status = await self.oracle.read(
                "getReporterLastTimestamp", _reporter=user
            )

            if last_timestamp is None:
                status.ok = False
                status.error = (
                    "Unable to retrieve reporter's last report timestamp:"
                    + read_status.error
                )
                status.e = read_status.e
                transaction_receipts.append((None, status))

            elif time.time() < last_timestamp + 43200:  # 43200 is 12 hours in seconds
                status.ok = False
                status.error = f"Address {user} is currently in reporter lock"
                transaction_receipts.append((None, status))

            else:

                logger.info(f"stake status: {is_staked[0]}")

                # Status 1: staked
                if is_staked[0] == 1:
                    jobs = []
                    for datafeed in self.datafeeds:
                        job = asyncio.create_task(datafeed.source.fetch_new_datapoint())
                        jobs.append(job)

                    _ = await asyncio.gather(*jobs)

                    for datafeed in self.datafeeds:

                        latest_data = datafeed.source.latest

                        if latest_data is not None:
                            query = datafeed.query

                            if query:
                                value = query.value_type.encode(latest_data[0])
                                query_id = query.query_id
                                query_data = query.query_data
                                extra_gas_price = 20

                                timestamp_count, read_status = await self.oracle.read(
                                    func_name="getTimestampCountById", _queryId=query_id
                                )

                                if not read_status.ok:
                                    status.error = (
                                        "Unable to retrieve timestampCount: "
                                        + read_status.error
                                    )  # error won't be none # noqa: E501
                                    status.e = read_status.e
                                    transaction_receipts.append((None, status))

                                tx_receipt, status = await self.oracle.write_with_retry(
                                    func_name="submitValue",
                                    gas_price=gas_price_gwei,
                                    extra_gas_price=extra_gas_price,
                                    retries=5,
                                    _queryId=query_id,
                                    _value=value,
                                    _nonce=timestamp_count,
                                    _queryData=query_data,
                                )

                                transaction_receipts.append((tx_receipt, status))

                            else:
                                logger.warning(
                                    f"Skipping submission for {repr(datafeed)}, "
                                    f"no query for datafeed."
                                )
                        else:
                            logger.warning(
                                f"Skipping submission for {repr(datafeed)}, "
                                f"datafeed value not updated."
                            )
                else:
                    # Status 3: disputed
                    if is_staked[0] == 3:
                        status.error = f"Addess {user} disputed. Switch address to continue reporting."  # noqa: E501
                        status.e = None
                        transaction_receipts.append((None, status))

                    # Status 0: not yet staked
                    elif is_staked[0] == 0:
                        logger.info("Depositing stake.")
                        _, write_status = await self.master.write_with_retry(
                            func_name="depositStake",
                            gas_price=gas_price_gwei,
                            extra_gas_price=20,
                            retries=retries,
                        )
                        if not write_status.ok:
                            status.error = (
                                "Unable to stake deposit: " + write_status.error
                            )  # error won't be none # noqa: E501
                            logger.error(status.error)
                            status.e = write_status.e
                            transaction_receipts.append((None, status))
                    # Statuses 2, 4, and 5: stake transition
                    else:
                        status.error = f"Address {user} is locked in dispute or for withdrawal."  # noqa: E501
                        status.e = None
                        transaction_receipts.append((None, status))

        return transaction_receipts

    async def report(self) -> None:
        """Submit latest values to the TellorX oracle every 10 seconds."""

        while True:
            _ = await self.report_once()
            await asyncio.sleep(10)

    def run(self) -> None:
        """Used by telliot CLI to update & submit data to TellorX Oracle."""

        # Create coroutines to run concurrently.
        loop = asyncio.get_event_loop()
        _ = loop.create_task(self.report())

        # Blocking loop.
        try:
            loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            loop.close()
