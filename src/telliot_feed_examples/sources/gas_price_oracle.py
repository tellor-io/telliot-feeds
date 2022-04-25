import json
from dataclasses import dataclass
from typing import Any, Dict
from typing import Optional

import requests
from requests import JSONDecodeError
from requests import Response
from requests.adapters import HTTPAdapter
from telliot_core.datasource import DataSource
from telliot_core.dtypes.datapoint import DataPoint
from telliot_core.dtypes.datapoint import datetime_now_utc
from urllib3.util import Retry

from telliot_feed_examples.utils.log import get_logger


logger = get_logger(__name__)
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["POST"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)


@dataclass
class GasPriceOracleSource(DataSource[str]):
    """DataSource for GasPriceOracle expected response data."""

    networks: Dict[int, str] = {
        1: "eth",
        56: "bsc",
        43114: "avax",
        250: "ftm",
        137: "poly",
        25: "cro",
        42220: "42220",
        128: "ht",
        1285: "movr",
        122: "fuse",
    }

    async def fetch_historical_gas_price(self, api_key:str, timestamp:int, chain_id:int) -> Optional[Response]:
        """Fetches historical gas price data from Owlracle API."""

        with requests.Session() as s:
            # s.mount("https://", adapter)
            s.mount("https://", adapter)
            json_data = {
                "apikey": api_key,
                "from": timestamp,
                "to": timestamp + 100,
            }
            try:
                return s.post(
                    f"https://owlracle.info/{self.networks[chain_id]}/history/",
                    headers={},
                    json=json_data,
                    timeout=0.5,
                )

            except requests.exceptions.RequestException as e:
                logger.error(f"GasPriceOracle API error: {e}")
                return None

    def adjust_data_types(self, data: list[dict[str, Any]]) -> list[str]:
        return [json.dumps(d) for d in data]

    async def fetch_new_datapoint(self) -> Optional[DataPoint[list[str]]]:
        """Retrieves historical gas prices from Owlracle API.

        Returns:
            float gas price in gwei, typically with one decimal place
        """
        rsp = await self.fetch_historical_gas_price()
        if rsp is None:
            logger.warning("No response from GasPriceOracle V1 API")
            return None, None

        try:
            historical_gas_prices = rsp.json()
        except JSONDecodeError as e:
            logger.error("GasPriceOracle source returned invalid JSON:", e.strerror)
            return None, None

        if gas_prices == []:
            logger.warning("GasPriceOracle source returned no historical gas prices.")
            return None, None

        gas_prices = []

        for i in historical_gas_prices:
            # find avg of high and low
            avg = (i["gasPrice"]["high"] + i["gasPrice"]["low"]) / 2

            gas_prices.append(avg)

        gas_prices.sort()
        
        gas_price_median = gas_prices[len(gas_prices)//2]

        gas_price_median = self.adjust_data_types(gas_price_median)
        datapoint = (gas_price_median, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"GasPriceOracle query V1 data retrieved at time {datapoint[1]}")

        return datapoint
