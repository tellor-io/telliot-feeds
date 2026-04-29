from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from decimal import InvalidOperation
from typing import Any
from typing import cast
from typing import Optional

import requests
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

BEA_API_URL = "https://apps.bea.gov/api/data"
NIPA_TABLE_NAME = "T20804"
PCE_LINE_NUMBER = "1"
PCE_AVERAGE_QUANT = Decimal("0.000000000000000001")


def load_bea_api_key() -> Optional[str]:
    """Load the BEA API key from telliot's api_keys.yaml config."""
    keys = TelliotConfig().api_keys
    for name in ("BEA", "bea"):
        api_keys = keys.find(name=name)
        if api_keys and api_keys[0].key:
            return cast(str, api_keys[0].key)
    return None


def _parse_month_period(period: Any) -> Optional[datetime]:
    """Parse BEA monthly periods such as 2026M01."""
    if not isinstance(period, str) or "M" not in period:
        return None

    year, month = period.split("M", maxsplit=1)
    try:
        return datetime(year=int(year), month=int(month), day=1)
    except ValueError:
        return None


def _parse_decimal(value: Any) -> Optional[Decimal]:
    """Parse BEA numeric strings, including comma-grouped values."""
    if value is None:
        return None

    try:
        return Decimal(str(value).replace(",", ""))
    except InvalidOperation:
        return None


@dataclass
class BEAPCESource(DataSource[Decimal]):
    """DataSource for the three-month moving average USPCE value from BEA."""

    api_key: Optional[str] = None
    url: str = BEA_API_URL
    table_name: str = NIPA_TABLE_NAME
    line_number: str = PCE_LINE_NUMBER
    year: str = "X"
    request_timeout: int = 10

    def get_pce_data(self) -> Optional[dict[str, Any]]:
        """Retrieve PCE price index data from the BEA NIPA API."""
        api_key = self.api_key or load_bea_api_key()
        if not api_key:
            logger.error("BEA API key not found in api_keys.yaml.")
            return None

        params = {
            "UserID": api_key,
            "datasetname": "NIPA",
            "method": "GetData",
            "TableName": self.table_name,
            "LineNumber": self.line_number,
            "Frequency": "M",
            "Year": self.year,
            "ResultFormat": "JSON",
        }

        try:
            with requests.Session() as session:
                response = session.get(self.url, params=params, timeout=self.request_timeout)
                response.raise_for_status()
                data = cast(dict[str, Any], response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving PCE data from BEA: {e}")
            return None
        except ValueError as e:
            logger.error(f"Error parsing BEA response JSON: {e}")
            return None

        return data

    def calculate_3month_average(self, data: dict[str, Any]) -> Optional[Decimal]:
        """Calculate the latest three-month average for headline PCE."""
        results = data.get("BEAAPI", {}).get("Results", {})
        rows = results.get("Data", [])
        values: list[tuple[datetime, str, Decimal]] = []

        notes = results.get("Notes", [])
        if notes and isinstance(notes[0], dict):
            logger.info(f"BEA PCE source note: {notes[0].get('NoteText')}")

        for row in rows:
            if not isinstance(row, dict) or str(row.get("LineNumber")) != self.line_number:
                continue

            raw_period = row.get("TimePeriod")
            period = _parse_month_period(raw_period)
            value = _parse_decimal(row.get("DataValue"))
            if period is None or value is None:
                continue

            values.append((period, str(raw_period), value))

        if len(values) < 3:
            logger.error("BEA response did not include at least three monthly PCE values.")
            return None

        latest_entries = sorted(values, key=lambda item: item[0])[-3:]
        averaged_values = ", ".join(f"{raw_period}={value}" for _, raw_period, value in latest_entries)
        logger.info(f"BEA PCE inputs for 3-month average: {averaged_values}")

        latest_values = [value for _, _, value in latest_entries]
        average = sum(latest_values, Decimal("0")) / Decimal(len(latest_values))
        return average.quantize(PCE_AVERAGE_QUANT)

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Decimal]:
        """Fetch, calculate, and store the latest USPCE datapoint."""
        data = self.get_pce_data()
        if data is None:
            return None, None

        average = self.calculate_3month_average(data)
        if average is None:
            return None, None

        datapoint = (average, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"USPCE {datapoint[0]} retrieved from BEA at time {datapoint[1]}")
        return datapoint
