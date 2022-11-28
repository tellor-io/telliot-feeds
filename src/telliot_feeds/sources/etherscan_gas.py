import json
import logging
from dataclasses import dataclass
from typing import List

import requests
from requests import JSONDecodeError
from requests.adapters import HTTPAdapter
from telliot_core.utils.timestamp import now
from urllib3.util import Retry

from telliot_feeds.datasource import DataSource
from telliot_feeds.datasource import OptionalDataPoint


logger = logging.getLogger(__name__)
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)


@dataclass
class EtherscanGasPrice:
    LastBlock: int
    SafeGasPrice: float
    ProposeGasPrice: float
    FastGasPrice: float
    suggestBaseFee: float
    gasUsedRatio: List[float]


@dataclass
class EtherscanGasPriceSource(DataSource[EtherscanGasPrice]):

    # Use an API key if higher rate limit is required
    api_key: str = ""

    async def fetch_new_datapoint(self) -> OptionalDataPoint[EtherscanGasPrice]:
        """Fetch new value and store it for later retrieval

        Gase prices are returned in gwei."""

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:77.0) Gecko/20190101 Firefox/77.0"}
        msg = "https://api.etherscan.io/api?module=gastracker&action=gasoracle"

        if self.api_key:
            msg = msg + f"&apikey={self.api_key}"

        with requests.Session() as s:
            s.mount("https://", adapter)

            try:
                rsp = s.get(msg, headers=headers)
            except requests.exceptions.ConnectTimeout as e:
                logger.error(f"Connection timeout: {e}")
                return None, None

            try:
                response = json.loads(rsp.content)
            except JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return None, None

            try:
                status = response["status"]
            except KeyError as e:
                logger.error(f"Key error: {e}")
                return None, None

            if int(status) == 1:
                gp_result = response["result"]
                gas_used_ratio_str = gp_result["gasUsedRatio"]
                gas_used_ratio = [float(num) for num in gas_used_ratio_str.split(",")]
                gp = EtherscanGasPrice(
                    LastBlock=int(gp_result["LastBlock"]),
                    SafeGasPrice=float(gp_result["SafeGasPrice"]),
                    ProposeGasPrice=float(gp_result["ProposeGasPrice"]),
                    FastGasPrice=float(gp_result["FastGasPrice"]),
                    suggestBaseFee=float(gp_result["suggestBaseFee"]),
                    gasUsedRatio=gas_used_ratio,
                )
                return gp, now()
            else:
                return None, None
