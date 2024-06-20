from dataclasses import dataclass
from dataclasses import field
from typing import Any
from urllib.parse import urlencode

from requests import Session
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
from requests.exceptions import TooManyRedirects
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

# Coingecko API uses an id for each token
# Source: see "API token list" https://www.coingecko.com/en/api/documentation
# Using a manual mapping for now.
coingecko_coin_id = {
    "bct": "toucan-protocol-base-carbon-tonne",
    "btc": "bitcoin",
    "dai": "dai",
    "eth": "ethereum",
    "idle": "idle",
    "mkr": "maker",
    "matic": "matic-network",
    "ric": "richochet",
    "sushi": "sushi",
    "trb": "tellor",
    "ohm": "olympus",
    "usdc": "usd-coin",
    "vsq": "vesq",
    "albt": "allianceblock",
    "rai": "rai",
    "xdai": "xdai",
    "avax": "avalanche",
    "aave": "aave",
    "badger": "badger-dao",
    "bch": "bitcoin-cash",
    "comp": "compound-governance-token",
    "crv": "curve-dao-token",
    "doge": "dogecoin",
    "dot": "polkadot",
    "eul": "euler",
    "fil": "filecoin",
    "gno": "gnosis",
    "link": "chainlink",
    "ltc": "litecoin",
    "shib": "shiba-inu",
    "uni": "uniswap",
    "usdt": "tether",
    "yfi": "yearn-finance",
    "steth": "staked-ether",
    "reth": "rocket-pool-eth",
    "op": "optimism",
    "grt": "the-graph",
    "pls": "pulsechain",
    "oeth": "origin-ether",
    "ousd": "origin-dollar",
    "sweth": "sweth",
    "wld": "worldcoin",
    "diva": "diva-protocol",
    "cbeth": "coinbase-wrapped-staked-eth",
    "wbeth": "wrapped-beacon-eth",
    "pyth": "pyth-network",
    "ogv": "origin-defi-governance",
    "ordi": "ordinals",
    "meth": "mantle-staked-ether",
    "wbtc": "wrapped-bitcoin",
    "mnt": "mantle",
    "usdy": "ondo-us-dollar-yield",
    "wmnt": "wrapped-mantle",
    "primeeth": "prime-staked-eth",
    "usdm": "usdm",
    "sdai": "savings-dai",
    "sfrax": "staked-frax",
    "frax": "frax",
    "gyd": "gyroscope-gyd",
    "frxeth": "frax-ether",
    "ezeth": "renzo-restaked-eth",
    "weeth": "wrapped-eeth",
    "wrseth": "wrapped-rseth",
    "rseth": "kelp-dao-restaked-eth",
    "mode": "mode",
    "tlos": "telos",
    "tara": "taraxa",
}

API_KEY = TelliotConfig().api_keys.find(name="coingecko")[0].key


class CoinGeckoSpotPriceService(WebPriceService):
    """CoinGecko Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "CoinGecko Price Service"
        if API_KEY == "":
            kwargs["url"] = "https://api.coingecko.com"
        else:
            kwargs["url"] = "https://pro-api.coingecko.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Coingecko API

        Note that coingecko does not return a timestamp so one is
        locally generated.
        """

        asset = asset.lower()
        currency = currency.lower()

        coin_id = coingecko_coin_id.get(asset, None)
        if not coin_id:
            raise Exception("Asset not supported: {}".format(asset))

        url_params = urlencode({"ids": coin_id, "vs_currencies": currency})
        request_url = self.url + "/api/v3/simple/price?{}".format(url_params)

        session = Session()
        if API_KEY != "":
            headers = {
                "Accepts": "application/json",
                "x-cg-pro-api-key": API_KEY,
            }
            session.headers.update(headers)

        try:
            response = session.get(request_url)

            if response.status_code >= 400:
                logger.warning(f"CoinGecko Error Status {response.status_code}: {response}")
                return None, None

            res = response.json()

        except (ConnectionError, Timeout, TooManyRedirects) as e:
            logger.warning(e)
            return None, None

        try:
            price = float(res[coin_id][currency])
            return price, datetime_now_utc()
        except KeyError as e:
            logger.error(f"Error parsing coingecko api response: KeyError: {e}")
            return None, None


@dataclass
class CoinGeckoSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: CoinGeckoSpotPriceService = field(default_factory=CoinGeckoSpotPriceService, init=False)


class CoinGeckoBRC20SpotPriceService(WebPriceService):
    """CoinGecko Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "CoinGecko Price Service"
        kwargs["url"] = "https://api.coingecko.com"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Coingecko API

        Note that coingecko does not return a timestamp so one is
        locally generated.
        """

        asset = asset.lower()
        currency = currency.lower()

        coin_id = coingecko_coin_id.get(asset, None)
        if not coin_id:
            raise Exception("Asset not supported: {}".format(asset))

        url_params = urlencode({"ids": coin_id, "vs_currencies": currency})
        request_url = "/api/v3/simple/price?{}".format(url_params)

        d = self.get_url(request_url)

        if "error" in d:
            if "api.coingecko.com used Cloudflare to restrict access" in str(d["exception"]):
                logger.warning("CoinGecko API rate limit exceeded")
            else:
                logger.error(d)
            return None, None
        elif "response" in d:
            response = d["response"]

            try:
                price = float(response[coin_id][currency])
                return price, datetime_now_utc()
            except KeyError as e:
                msg = "Error parsing Coingecko API response: KeyError: {}".format(e)
                logger.error(msg)
                return None, None

        else:
            msg = "Invalid response from get_url"
            logger.error(msg)
            return None, None


@dataclass
class CoinGeckoBRC20SpotPriceSource(PriceSource):
    identifier: str = ""
    asset: str = ""
    currency: str = ""
    unit: str = ""
    service: CoinGeckoBRC20SpotPriceService = field(default_factory=CoinGeckoBRC20SpotPriceService, init=False)
