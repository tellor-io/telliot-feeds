from __future__ import annotations

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
    allowed_methods=["GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)


@dataclass
class MimicryCollectionStatSource(DataSource[str]):
    """DataSource for MimicryCollectionStat expected response data."""

    chainId: Optional[int] = None
    collectionAddress: Optional[str] = None
    metric: Optional[int] = None

    async def fetch_mimicry_api(self) -> Optional[Response]:
        """
        Request data from hosted api

        see https://github.com/Mimicry-Protocol/TAMI/
        """

        if self.collectionAddress is not None:
            self.collectionAddress = self.collectionAddress.lower()

        url = f"http://50.112.84.236:3000/api/stats?address={self.collectionAddress}&stat={self.metric}"

        with requests.Session() as s:
            s.mount("https://", adapter)
            try:
                return s.get(url=url, timeout=10)

            except requests.exceptions.RequestException as e:
                logger.error(f"Mimicry API error: {e}")
                return None

            except requests.exceptions.Timeout as e:
                logger.error(f"Mimicry API timed out: {e}")
                return None

    async def fetch_new_datapoint(
        self,
    ) -> OptionalDataPoint[Any]:
        """
        Calculates desired metric for a collection on the chosen chain id.

        Returns:
            float -- the desired metric
        """

        if not self.collectionAddress:
            logger.error("Missing a collection address for Mimicry NFT index calculation")
            return None, None

        if self.metric is None:
            logger.error("Missing a metric for Mimicry NFT index calculation")
            return None, None

        rsp = await self.fetch_mimicry_api()

        if rsp is None:
            logger.warning("No response from Mimicry API")
            return None, None

        if rsp.status_code // 100 != 2:
            logger.warning("Invalid response from Mimicry API: " + str(rsp.status_code))
            return None, None

        try:
            mimicry_dict = rsp.json()
        except JSONDecodeError as e:
            logger.error("Mimicry API returned invalid JSON:", e.strerror)
            return None, None

        if mimicry_dict == {}:
            logger.warning("Mimicry API returned no data.")
            return None, None

        try:
            mimicry_stat = mimicry_dict["value"]
        except KeyError:
            logger.error("Unable to parse Mimicry API JSON response")
            return None, None

        datapoint = (mimicry_stat, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(
            f"""
            Mimicry API data retrieved at time
            {datapoint[1]} for metric {self.metric}
            on collection {self.collectionAddress}
            """
        )

        return datapoint
