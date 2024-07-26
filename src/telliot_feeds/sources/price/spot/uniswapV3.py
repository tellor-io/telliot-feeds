from dataclasses import dataclass
from dataclasses import field
from typing import Any

import requests
from requests import Session
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)
uniswapV3_map = {
    "eth": "0x0000000000000000000000000000000000000000",
    "wbtc": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    "matic": "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0",
    "dai": "0x6b175474e89094c44da98b954eedeac495271d0f",
    "fuse": "0x970b9bb2c0444f5e81e9d0efb84c8ccdcdcaf84d",
    "steth": "0xae7ab96520de3a18e5e111b5eaab095312d7fe84",
    "reth": "0xae78736cd615f374d3085123a210448e74fc6393",
    "pls": "0xa882606494d86804b5514e07e6bd2d6a6ee6d68a",
    "sweth": "0xf951e335afb289353dc249e82926178eac7ded78",
    "cbeth": "0xbe9895146f7af43049ca1c1ae358b0541ea49704",
    "oeth": "0x856c4efb76c1d1ae02e20ceb03a2a6a08b0b8dc3",
    "wbtc": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    "mnt": "0x3c3a81e81dc49a522a592e7622a7e711c06bf354",
    "frax": "0x853d955acef822db058eb8505911ed77f175b99e",
    "ezeth": "0xbf5495efe5db9ce00f80364c8b423567e58d2110",
    "weeth": "0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee",
    "wrseth": "0xd2671165570f41bbb3b0097893300b6eb6101e6c",
    "rseth": "0xa1290d69c65a6fe4df752f95823fae25cb99e5a7",
}

API_KEY = TelliotConfig().api_keys.find(name="thegraph")[0].key


class UniswapV3PriceService(WebPriceService):
    """UniswapV3 Price Service in USD and ETH"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "UniswapV3 Price Service"
        kwargs["url"] = "https://gateway-arbitrum.network.thegraph.com"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the UniswapV3 subgraph
        https://docs.uniswap.org/sdk/subgraph/subgraph-examples

        """

        asset = asset.lower()

        token = uniswapV3_map.get(asset, None)
        if not token:
            raise Exception("Asset not supported: {}".format(asset))

        query = "{bundles{id ethPriceUSD}token" + f'(id: "{token}")' + "{ derivedETH } }"

        json_data = {"query": query}

        request_url = f"{self.url}/api/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"

        session = Session()
        if API_KEY != "":
            headers = {"Accepts": "application/json", "Authorization": f"Bearer {API_KEY}"}
            session.headers.update(headers)
        if API_KEY == "":
            logger.warning("No Graph API key found for Uniswap prices!")

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=self.timeout)
                res = r.json()
                data = {"response": res}

            except requests.exceptions.ConnectTimeout:
                logger.warning("Timeout Error, No Uniswap prices retrieved (check thegraph api key)")
                return None, None

            except Exception as e:
                logger.warning(f"No prices retrieved from Uniswap: {e}")
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
                    msg = "Uniswap API not included, because price response is 0"
                    logger.warning(msg)
                    return None, None
                else:
                    return price, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing UniswapV3 response: KeyError: {}".format(e)
                logger.critical(msg)
                return None, None

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class UniswapV3PriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: UniswapV3PriceService = field(default_factory=UniswapV3PriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        price_source = UniswapV3PriceSource(asset="reth", currency="eth")
        price, timestamp = await price_source.fetch_new_datapoint()
        print(price, timestamp)

    asyncio.run(main())
