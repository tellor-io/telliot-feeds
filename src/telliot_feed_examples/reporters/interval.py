""" BTCUSD Price Reporter

Example of a subclassed Reporter.
"""
import asyncio
import time
from typing import Any
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
        datafeed: DataFeed[Any],
    ) -> None:

        self.endpoint = endpoint
        self.master = master
        self.oracle = oracle
        self.datafeed = datafeed
        self.user = self.endpoint.web3.eth.account.from_key(private_key).address

        logger.info(f"Reporting with account: {self.user}")

    async def ensure_staked(self, gas_price_gwei: int) -> Tuple[bool, ResponseStatus]:
        """Make sure the current user is staked."""
        status = ResponseStatus()

        staker_info, read_status = await self.master.read(
            "getStakerInfo", _staker=self.user
        )

        if (not read_status.ok) or (staker_info is None):
            status.ok = False
            status.error = (
                "unable to read reporters staker status: " + read_status.error
            )  # error won't be none # noqa: E501
            status.e = read_status.e
            return False, status

        logger.info(f"Stake status: {staker_info[0]}")

        # Status 1: staked
        if staker_info[0] == 1:
            return True, status

        # Status 0: not yet staked
        elif staker_info[0] == 0:
            logger.info("Address not yet staked. Depositing stake.")

            _, write_status = await self.master.write_with_retry(
                func_name="depositStake", gas_price=gas_price_gwei, extra_gas_price=20
            )

            if write_status.ok:
                return True, status
            else:
                status.error = (
                    "Unable to stake deposit: " + write_status.error
                )  # error won't be none # noqa: E501
                logger.error(status.error)
                status.e = write_status.e
                return False, status

        # Status 3: disputed
        if staker_info[0] == 3:
            status.error = f"Addess {self.user} disputed. Switch address to continue reporting."  # noqa: E501
            logger.error(status.error)
            status.e = None
            return False, status

        # Statuses 2, 4, and 5: stake transition
        else:
            status.error = f"Address {self.user} is locked in dispute or for withdrawal."  # noqa: E501
            logger.error(status.error)
            status.e = None
            return False, status

    async def check_reporter_lock(self) -> Tuple[bool, ResponseStatus]:
        """Make sure reporter's not locked."""
        status = ResponseStatus()

        last_timestamp, read_status = await self.oracle.read(
            "getReporterLastTimestamp", _reporter=self.user
        )

        if (not read_status.ok) or (last_timestamp is None):
            status.ok = False
            status.error = (
                "Unable to retrieve reporter's last report timestamp:"
                + read_status.error
            )
            logger.error(status.error)
            status.e = read_status.e
            return True, status

        if time.time() < last_timestamp + 43200:  # 43200 is 12 hours in seconds
            status.ok = False
            status.error = f"Address {self.user} is currently in reporter lock"
            return True, status

        return False, status

    async def ensure_profitable(
        self, gas_price_gwei: int
    ) -> Tuple[bool, ResponseStatus]:
        """Make sure the submission would be profitable."""
        status = ResponseStatus()
        # Get current tips and time-based reward for given queryID
        rewards, read_status = await self.oracle.read(
            "getCurrentReward", _queryId=self.datafeed.query.query_id
        )

        if (not read_status.ok) or (rewards is None):
            status.ok = False
            status.error = (
                "Unable to retrieve queryID's current rewards:" + read_status.error
            )
            logger.error(status.error)
            status.e = read_status.e
            return False, status

        tips, tb_reward = rewards
        gas = 500000  # Taken from telliot-core contract write, TODO: optimize

        logger.info(
            f"""
            current tips: {tips}
            current tb_reward: {tb_reward}
            gas: {gas}
            gas_price_gwei: {gas_price_gwei}
            """
        )

        profit = tb_reward + tips - (gas * gas_price_gwei)
        logger.info(f"Estimated profit: {profit}")

        return profit > 0, status

    async def report_once(
        self,
    ) -> Tuple[Optional[AttributeDict[Any, Any]], ResponseStatus]:
        """Submit value once"""
        # TODO: use maxGas var passed from CLI
        gas_price_gwei = await fetch_gas_price()

        # TODO: save current reporter staked as class attr
        # to reduce web3 calls
        staked, status = await self.ensure_staked(gas_price_gwei)
        if not staked:
            return None, status

        # TODO: save last_timestamp as class attr
        # to reduce web3 calls
        reporter_locked, status = await self.check_reporter_lock()
        if reporter_locked:
            return None, status

        profitable, status = await self.ensure_profitable(gas_price_gwei)
        if not profitable:
            return None, status

        status = ResponseStatus()

        await self.datafeed.source.fetch_new_datapoint()
        latest_data = self.datafeed.source.latest

        if latest_data is None:
            logger.warning(
                f"Skipping submission for {repr(self.datafeed)}, "
                f"datafeed value not updated."
            )
            return None, status

        query = self.datafeed.query

        value = query.value_type.encode(latest_data[0])
        query_id = query.query_id
        query_data = query.query_data
        extra_gas_price = 20

        timestamp_count, read_status = await self.oracle.read(
            func_name="getTimestampCountById", _queryId=query_id
        )

        if not read_status.ok:
            status.error = (
                "Unable to retrieve timestampCount: " + read_status.error
            )  # error won't be none # noqa: E501
            logger.error(status.error)
            status.e = read_status.e
            return None, status

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

        return tx_receipt, status

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
