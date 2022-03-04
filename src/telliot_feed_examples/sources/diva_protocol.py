from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import Any

from telliot_core.datasource import DataSource
from telliot_core.dtypes.datapoint import DataPoint

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class DivaManualSource(DataSource[Any]):
    """DataSource for Diva Protocol manually-entered data."""

    reference_asset: str = ""
    timestamp: int = 0

    def parse_user_val(self) -> float:
        """Parse historical price from user input."""
        print(
            "Enter price to report for reference asset "
            f"{self.reference_asset} at timestamp {self.timestamp}:"
        )

        data = None
        while data is None:
            inpt = input()

            try:
                inpt = float(inpt)  # type: ignore
            except ValueError:
                print("Invalid input. Enter decimal value (float).")
                continue

            print(f"Submitting value: {inpt}\nPress [ENTER] to confirm.")
            _ = input()
            data = inpt

        return data

    async def fetch_new_datapoint(self) -> DataPoint[float]:
        """Update current value with time-stamped value fetched from user input.

        Returns:
            Current time-stamped value
        """
        data = self.parse_user_val()
        dt = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)
        datapoint = (data, dt)

        self.store_datapoint(datapoint)

        logger.info(f"Stored price of {self.reference_asset} at {dt}: {data}")

        return datapoint
