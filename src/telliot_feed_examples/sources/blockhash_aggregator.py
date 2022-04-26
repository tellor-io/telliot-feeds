from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Optional

import requests
from telliot_core.datasource import DataSource
from telliot_core.dtypes.datapoint import DataPoint
from web3 import Web3

from telliot_feed_examples.utils.cfg import mainnet_config
from telliot_feed_examples.utils.log import get_logger

logger = get_logger(__name__)


cfg = mainnet_config()
cfg.get_endpoint().connect()
w3 = cfg.get_endpoint().web3


@dataclass
class TellorRNGManualSource(DataSource[Any]):
    """DataSource for TellorRNG manually-entered timestamp."""

    timestamp = 0

    def parse_user_val(self) -> int:
        """Parse timestamp from user input."""
        print("Enter timestamp for generating a random number: ")

        data = None
        while data is None:
            inpt = input()

            try:
                inpt = int(inpt)  # type: ignore
            except ValueError:
                print("Invalid input. Enter decimal value (int).")
                continue

            print(
                "Generating random number from timestamp: "
                f"{inpt}\nPress [ENTER] to confirm."
            )
            _ = input()
            data = inpt

        self.timestamp = data
        return data

    def getEthHashByTimestamp(self, timestamp: int) -> Optional[str]:
        """Fetches next Ethereum blockhash after timestamp from API."""
        try:
            this_block = w3.eth.get_block("latest")
            if this_block is None:
                return None
            if this_block["timestamp"] < timestamp:
                return None
            else:
                min_num: int = 0
                max_num: int = this_block["number"]
                mid_num: int = 0
                while max_num - min_num > 1:
                    mid_num = round((max_num + min_num) / 2)
                    this_block = w3.eth.get_block(mid_num)
                    if this_block is None:
                        return None
                    if this_block["timestamp"] > timestamp:
                        max_num = mid_num
                    else:
                        min_num = mid_num
                this_block = w3.eth.get_block(max_num)
                if this_block is None:
                    return None
                return str(this_block["hash"].hex())
        except Exception as e:
            logger.error(f"Tellor RNG V1 ethereum API error: {e}")
            return None

    def getBtcHashByTimestamp(self, timestamp: int) -> Optional[str]:
        """Fetches next Bitcoin blockhash after timestamp from API."""

        with requests.Session() as s:
            try:
                this_block = s.get("https://blockchain.info/latestblock").json()
                if this_block is None:
                    logger.error("Tellor RNG V1 no latest btc block returned from API")
                    return ""
                if this_block["time"] < timestamp:
                    logger.error(
                        f"Tellor RNG V1 current btc block time, {this_block['time']}"
                        + f"is less than given timestamp {timestamp}"
                    )
                    return ""
                else:
                    min_num: int = 0
                    max_num: int = this_block["height"]
                    mid_num: int = 0
                    while max_num - min_num > 1:
                        mid_num = round((max_num + min_num) / 2)
                        this_block = s.get(
                            f"https://blockchain.info/rawblock/{mid_num}"
                        ).json()
                        if this_block is None:
                            return None
                        if this_block["time"] > timestamp:
                            max_num = mid_num
                        else:
                            min_num = mid_num
                    this_block = s.get(
                        f"https://blockchain.info/rawblock/{max_num}"
                    ).json()
                    if this_block is None:
                        return None
                    return str(this_block["hash"])
            except requests.exceptions.RequestException as e:
                logger.error(f"Tellor RNG V1 bitcoin API error: {e}")
                return ""

    async def fetch_new_datapoint(self) -> DataPoint[bytes]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """

        if self.timestamp == 0:
            timestamp = self.parse_user_val()
        else:
            timestamp = self.timestamp
        eth_hash = self.getEthHashByTimestamp(timestamp)
        btc_hash = self.getBtcHashByTimestamp(timestamp)

        if eth_hash is None:
            logger.warning("No response from TellorRNG V1 Ethereum API")
            return None, None
        if btc_hash is None:
            logger.warning("No response from TellorRNG V1 Bitcoin API")
            return None, None

        data = Web3.solidityKeccak(["string", "string"], [eth_hash, str(btc_hash)])
        dt = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)
        datapoint = (data, dt)

        self.store_datapoint(datapoint)

        logger.info(f"Stored random number for timestamp {timestamp}: {data}")

        return datapoint
