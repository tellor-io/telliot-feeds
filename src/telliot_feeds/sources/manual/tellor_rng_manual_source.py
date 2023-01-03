from dataclasses import dataclass

from eth_abi import encode_single
from eth_abi.exceptions import ValueOutOfBounds

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.input_timeout import input_timeout
from telliot_feeds.utils.input_timeout import TimeoutOccurred
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class TellorRNGManualInputSource(DataSource[bytes]):
    """Manual input source for query type TellorRNG's value response"""

    def parse_user_input(self) -> bytes:
        """Handle user input"""
        print("Type in your TellorRNG response as a hex string (example: 0x2b563420722cbcfc84857129bef775e0dc5f1401):")
        response = None

        while response is None:
            user_input = input_timeout()
            if len(user_input) < 2:
                print(
                    "Invalid input! Not enough characters, "
                    + "Enter a hex string (example: 0x2b563420722cbcfc84857129bef775e0dc5f1401)"
                )
                continue
            if user_input[:2] == "0x":
                user_input = user_input[2:]
            try:
                val = bytes.fromhex(user_input)
                encode_single("bytes32", val)
            except ValueOutOfBounds:
                print("Invalid input! Exceeds total byte size for bytes32 encoding")
                continue
            except ValueError:
                print("Invalid input! Enter hex string value (32 byte size).")
                continue
            print(f"\nTellorRNG value to be submitted on chain: {user_input}")
            print("Press [ENTER] to continue")
            _ = input_timeout()
            response = val

        return response

    async def fetch_new_datapoint(self) -> OptionalDataPoint[bytes]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """
        try:
            response = self.parse_user_input()
        except TimeoutOccurred:
            logger.info("Timeout occurred while waiting for user input")
            return None, None

        datapoint = (response, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"TellorRNG value {datapoint[0]!r} submitted at time {datapoint[1]}")

        return datapoint
