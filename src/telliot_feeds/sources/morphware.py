import json
from dataclasses import dataclass
from typing import Any
from typing import Optional

import requests
from requests import JSONDecodeError
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["POST"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)


@dataclass
class MorphwareV1Source(DataSource[str]):
    """DataSource for Morphware query V1 expected response data."""

    async def get_metadata(self) -> Optional[Response]:
        """Fetches EC2 metadata from Morphware API."""

        with requests.Session() as s:
            # s.mount("https://", adapter)
            s.mount("http://", adapter)
            json_data = {
                "provider": "amazon",
                "service": "compute",
                "region": "us-east-1",
            }
            try:
                return s.post(
                    "http://167.172.239.133:5000/products-2",
                    headers=None,
                    json=json_data,
                    timeout=0.5,
                )

            except requests.exceptions.RequestException as e:
                logger.error(f"Morphware V1 API error: {e}")
                return None

    def adjust_data_types(self, data: list[dict[str, Any]]) -> list[str]:
        return [json.dumps(d) for d in data]

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Any]:
        """Retrieves Amazon EC2 instance pricing metadata from API
        hosted by Morphware.

        Returns:
            array of JSON object strings containing EC2 metadata:
            Interface Ec2MetaData {
                        "Instance Type": str,
                        "CUDA Cores": int,
                        "Number of CPUs": int,
                        "RAM": float,
                        "On-demand Price per Hour": float,
                    }
        """
        rsp = await self.get_metadata()
        if rsp is None:
            logger.warning("No response from Morphware V1 API")
            return None, None

        try:
            ec2_metadata = rsp.json()
        except JSONDecodeError as e:
            logger.error("Morphware V1 source returned invalid JSON:", e.strerror)
            return None, None

        if ec2_metadata == []:
            logger.warning("Morphware V1 source returned no EC2 metadata")
            return None, None

        ec2_metadata = self.adjust_data_types(ec2_metadata)
        datapoint = (ec2_metadata, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"Morphware query V1 data retrieved at time {datapoint[1]}")

        return datapoint
