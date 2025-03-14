import time
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional

import requests
from requests import Session
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

GYD_USDC_POOL_ADDRESS = "0xC2AA60465BfFa1A88f5bA471a59cA0435c3ec5c1"
GYD_USDT_POOL_ADDRESS = "0xfbfaD5fa9E99081da6461F36f229B5cC88A64c63"
GYD_SDAI_POOL_ADDRESS = "0x2191Df821C198600499aA1f0031b1a7514D7A7D9"

API_KEY = TelliotConfig().api_keys.find(name="thegraph")[0].key


class gydSpotPriceService(WebPriceService):
    """Custom GYD Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom GYD Price Service"
        kwargs["url"] = ""
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    async def get_spot_from_pool(self, contractAddress: str) -> Optional[float]:
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get balancer prices")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to balancer prices")
            return None
        w3 = ep.web3

        # calls the getPrice() read function from a balancer pool to get the price
        # of gyd priced in the other asset in the pool
        gyd_priced_in_currency = w3.eth.call(
            {
                "to": contractAddress,
                "data": "0x98d5fdca",
            }
        )

        gyd_currency_price_decoded = w3.to_int(gyd_priced_in_currency)
        gyd_priced_in_currency = w3.from_wei(gyd_currency_price_decoded, "ether")
        gyd_priced_in_currency_float: Optional[float] = float(gyd_priced_in_currency)

        if contractAddress.lower() == GYD_SDAI_POOL_ADDRESS.lower():
            from telliot_feeds.feeds.sdai_usd_feed import sdai_usd_median_feed

            currency_spot_price, timestamp = await sdai_usd_median_feed.source.fetch_new_datapoint()
        elif contractAddress.lower() == GYD_USDC_POOL_ADDRESS.lower():
            from telliot_feeds.feeds.usdc_usd_feed import usdc_usd_median_feed

            currency_spot_price, timestamp = await usdc_usd_median_feed.source.fetch_new_datapoint()
        elif contractAddress.lower() == GYD_USDT_POOL_ADDRESS.lower():
            from telliot_feeds.feeds.usdt_usd_feed import usdt_usd_median_feed

            currency_spot_price, timestamp = await usdt_usd_median_feed.source.fetch_new_datapoint()
        else:
            print("Returning from inside the else statement after getting the currency spot price")
            return None

        print(
            f"GYD/currency: {gyd_priced_in_currency}, coingecko currency price: {currency_spot_price}, at {timestamp}"
        )
        if currency_spot_price is not None and gyd_priced_in_currency_float is not None:
            return gyd_priced_in_currency_float / currency_spot_price
        else:
            return None

    # https://gateway-arbitrum.network.thegraph.com/api/%5BAPI-KEY%5D/subgraphs/id/C4ayEZP2yTXRAB8vSaTrgN4m9anTe9Mdm2ViyiAuV9TV
    async def get_total_liquidity_of_pools(self) -> list[float]:
        baseURL = "https://gateway-arbitrum.network.thegraph.com"
        gyd_token_contract_address = "0xe07F9D810a48ab5c3c914BA3cA53AF14E4491e8A"

        query = (
            "{pools(where: {tokensList_contains: ["
            + f'"{gyd_token_contract_address}"'
            + "] } )"
            + "{ address, id, name, totalLiquidity } }"
        )

        json_data = {"query": query}

        request_url = f"{baseURL}/api/subgraphs/id/C4ayEZP2yTXRAB8vSaTrgN4m9anTe9Mdm2ViyiAuV9TV"

        session = Session()
        if API_KEY != "":
            headers = {"Accepts": "application/json", "Authorization": f"Bearer {API_KEY}"}
            session.headers.update(headers)
        if API_KEY == "":
            logger.warning("No Graph API key found for Balancer data!")

        with requests.Session() as s:
            try:
                r = s.post(request_url, headers=headers, json=json_data, timeout=self.timeout)
                res = r.json()
                data = {"response": res}
            except requests.exceptions.ConnectTimeout:
                logger.warning("Timeout Error, No data retrieved from Balancer subgraph")
                return []

            except Exception as e:
                logger.warning(f"No data retrieved from Balancer subgraph {e}")
                return []

        if "error" in data:
            logger.error(data)
            return []

        elif "response" in data:
            response = data["response"]

            try:
                gyd_usdc_liquidity = 0
                gyd_usdt_liquidity = 0
                gyd_sdai_liquidity = 0
                poolsArr = response["data"]["pools"]
                for d in poolsArr:
                    if d["address"].lower() == GYD_SDAI_POOL_ADDRESS.lower():
                        gyd_sdai_liquidity = d["totalLiquidity"]
                    elif d["address"].lower() == GYD_USDC_POOL_ADDRESS.lower():
                        gyd_usdc_liquidity = d["totalLiquidity"]
                    elif d["address"].lower() == GYD_USDT_POOL_ADDRESS.lower():
                        gyd_usdt_liquidity = d["totalLiquidity"]

                return [
                    float(gyd_usdc_liquidity),
                    float(gyd_usdt_liquidity),
                    float(gyd_sdai_liquidity),
                    float(gyd_usdc_liquidity) + float(gyd_usdt_liquidity) + float(gyd_sdai_liquidity),
                ]
            except KeyError as e:
                msg = "Error parsing BalancerV2 response: KeyError: {}".format(e)
                logger.critical(msg)
                return []

        else:
            raise Exception("Invalid response from get_url")

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implemenation gets the price from 3 balancer pools and coingecko"""

        asset = asset.lower()
        currency = currency.lower()

        if currency != "usd":
            logger.error("GYD price service only works for usd")
            return None, None

        gyd_from_usdc_pool = None
        gyd_from_usdt_pool = None
        gyd_from_sdai_pool = None

        try:
            logger.info("Gathering prices from Balancer pools...")
            gyd_from_usdc_pool = await self.get_spot_from_pool(GYD_USDC_POOL_ADDRESS)
            gyd_from_usdt_pool = await self.get_spot_from_pool(GYD_USDT_POOL_ADDRESS)
            gyd_from_sdai_pool = await self.get_spot_from_pool(GYD_SDAI_POOL_ADDRESS)

            logger.info("Gathering liquidity data from Balancer pools...")
            liquidity_data = await self.get_total_liquidity_of_pools()
            gyd_usdc_weight = liquidity_data[0] / liquidity_data[3]
            gyd_usdt_weight = liquidity_data[1] / liquidity_data[3]
            gyd_sdai_weight = liquidity_data[2] / liquidity_data[3]
        except IndexError:
            logger.warning("Rate limit or theGraph API key not found. Sleeping for 10 seconds...")
            time.sleep(10)
            return None, None

        except Exception as e:
            logger.warning(f"Problem retrieving Balancer pool data: {e}")

        if gyd_from_usdc_pool == 0 or gyd_from_usdt_pool == 0 or gyd_from_sdai_pool == 0:
            logger.warning("Balancer pool price is 0, returning None")
            return None, None

        if gyd_from_usdc_pool is not None and gyd_from_usdt_pool is not None and gyd_from_sdai_pool is not None:
            gyd_weighted_price = (
                (gyd_usdc_weight) * (gyd_from_usdc_pool)
                + (gyd_usdt_weight) * (gyd_from_usdt_pool)
                + (gyd_sdai_weight) * (gyd_from_sdai_pool)
            )
            print(f"GYD weighted price: {gyd_weighted_price}")
            timestamp = datetime_now_utc()
            return gyd_weighted_price, timestamp
        else:
            return None, None


@dataclass
class gydCustomSpotPriceSource(PriceSource):
    """ "Gets data from Balancer pools and coingecko and aggregates the data to return a spot price"""

    asset: str = "gyd"
    currency: str = "usd"
    service: gydSpotPriceService = field(default_factory=gydSpotPriceService, init=False)
