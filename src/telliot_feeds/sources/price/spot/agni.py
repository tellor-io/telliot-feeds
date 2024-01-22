from dataclasses import dataclass
from dataclasses import field
from typing import Any

import requests

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)
agniFinance_map = {
    "weth": "0xdeaddeaddeaddeaddeaddeaddeaddeaddead1111",
    "meth": "0xcda86a272531e8640cd7f1a92c01839911b90bb0",
    "usdy": "0x5be26527e817998a7206475496fde1e68957c5a6",
    "wmnt": "0x78c1b0c915c4faa5fffa6cabf0219da63d7f4cb8",
    "wbtc": "0xcabae6f6ea1ecab08ad02fe02ce9a44f09aebfa2",
    "usdt": "0x201eba5cc46d216ce6dc03f6a759e8e766e956ae",
    "usdc": "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9",
}


class agniFinancePriceService(WebPriceService):
    """agniFinance Price Service in USD and ETH"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "agniFinance subgraph"
        kwargs["url"] = "https://agni.finance"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the agniFinance subgraph
        https://agni.finance/graph/subgraphs/name/agni/exchange-v3/graphql?
        """

        asset = asset.lower()

        token = agniFinance_map.get(asset, None)
        if not token:
            raise Exception("Asset not supported: {}".format(asset))

        headers = {
            "Content-Type": "application/json",
        }

        query = "{bundles{id ethPriceUSD}token" + f'(id: "{token}")' + "{ derivedETH } }"

        json_data = {"query": query}

        request_url = self.url + "/graph/subgraphs/name/agni/exchange-v3"

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=self.timeout)
                res = r.json()
                data = {"response": res}

            except requests.exceptions.ConnectTimeout:
                logger.warning("Timeout Error, No prices retrieved from AGNI Finance")
                return None, None

            except Exception:
                logger.warning("No prices retrieved from AGNI Finance")
                return None, None

        if "error" in data:
            logger.error(data)
            return None, None

        elif "response" in data:
            response = data["response"]

            try:
                ethprice = float(response["data"]["bundles"][0]["ethPriceUSD"])
                if asset.lower() == "eth":
                    token_data = 1
                elif currency.lower() == "eth":
                    ethprice = 1
                    token_data = response["data"]["token"]["derivedETH"]
                else:
                    token_data = response["data"]["token"]["derivedETH"]
                price = ethprice * float(token_data)
                if price == 0.0:
                    msg = "AGNI Finance API not included, because price response is 0"
                    logger.warning(msg)
                    return None, None
                else:
                    return price, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing AGNI Finance response: KeyError: {}".format(e)
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class agniFinancePriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: agniFinancePriceService = field(default_factory=agniFinancePriceService, init=False)
