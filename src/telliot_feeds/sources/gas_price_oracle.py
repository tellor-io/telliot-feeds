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
class GasPriceOracleSource(DataSource[str]):
    """DataSource for GasPriceOracle expected response data."""

    chainId: Optional[int] = None
    timestamp: Optional[int] = None

    async def fetch_historical_gas_price(
        self,
    ) -> Optional[Response]:
        """Fetches historical gas price data from Owlracle API."""

        if self.chainId is not None and self.timestamp is not None:
            networks = {
                1: "eth",
                56: "bsc",
                43114: "avax",
                250: "ftm",
                137: "poly",
                25: "cro",
                42220: "one",
                128: "ht",
                1285: "movr",
                122: "fuse",
            }

            url = (
                f"https://owlracle.info/"
                f"{networks[self.chainId]}"
                "/history?"
                f"from={int(self.timestamp)}"
                f"&to={int(self.timestamp) + 100}"
            )

            with requests.Session() as s:
                s.mount("https://", adapter)
                try:
                    return s.get(url=url, timeout=0.5, headers={"User-Agent": "Custom"})

                except requests.exceptions.RequestException as e:
                    logger.error(f"GasPriceOracle API error: {e}")
                    return None

                except requests.exceptions.Timeout as e:
                    logger.error(f"GasPriceOracle API timed out: {e}")
                    return None

        else:
            logger.warning("Can't fetch data: GasPriceOracle DataSource QueryParameters unset")
            return None

    async def fetch_new_datapoint(
        self,
    ) -> OptionalDataPoint[Any]:
        """Retrieves historical gas prices from Owlracle API.

        Returns:
            float gas price in gwei, typically with one decimal place
        """
        rsp = await self.fetch_historical_gas_price()
        if rsp is None:
            logger.warning("No response from GasPriceOracle API")
            return None, None

        if rsp.status_code // 100 != 2:
            logger.warning("Invalid response from GasPriceOracle API: " + str(rsp.status_code))
            return None, None

        try:
            historical_gas_prices = rsp.json()
        except JSONDecodeError as e:
            logger.error("GasPriceOracle source returned invalid JSON:", e.strerror)
            return None, None

        if historical_gas_prices == []:
            logger.warning("GasPriceOracle source returned no historical gas prices.")
            return None, None

        gas_prices = []

        try:
            for i in historical_gas_prices:
                # find avg of high and low
                avg = (i["gasPrice"]["high"] + i["gasPrice"]["low"]) / 2

                gas_prices.append(avg)
        except KeyError:
            logger.error("Unable to parse GasPriceOracle source JSON")
            return None, None
        except ValueError:
            logger.error("Unable to calculate median gas price from GasPriceOracle source JSON")
            return None, None
        gas_prices.sort()

        gas_price_median = gas_prices[len(gas_prices) // 2]

        datapoint = (gas_price_median, datetime_now_utc())
        self.store_datapoint(datapoint)

        logger.info(f"GasPriceOracle query V1 data retrieved at time {datapoint[1]}")

        return datapoint
