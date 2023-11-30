from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.maverickV2 import MaverickV2PriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class oethEthService(WebPriceService):
    """Calculate OETH/ETH based on MaverickV2 and converted OETH/USD price sources"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "oeth/eth Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    async def get_oeth_usd(self) -> OptionalDataPoint[float]:
        oeth_usd_source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="oeth", currency="usd"),
                UniswapV3PriceSource(asset="eth", currency="oeth"),
            ],
        )

        oeth_usd_price = await oeth_usd_source.fetch_new_datapoint()
        if oeth_usd_price is None:
            logger.error("Unable to get oeth/usd sources to convert.")
            return None, None
        print(oeth_usd_price)
        return oeth_usd_price

    async def get_eth_usd(self) -> OptionalDataPoint[float]:
        eth_usd_source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="eth", currency="usd"),
                CoinbaseSpotPriceSource(asset="eth", currency="usd"),
                GeminiSpotPriceSource(asset="eth", currency="usd"),
                KrakenSpotPriceSource(asset="eth", currency="usd"),
            ],
        )

        eth_usd_price = await eth_usd_source.fetch_new_datapoint()
        if eth_usd_price is None:
            logger.error("Unable to get eth/usd price for converting oeth/usd sources.")
            return None, None
        print(eth_usd_price)
        return eth_usd_price

    async def get_oeth_eth_mav(self) -> OptionalDataPoint[float]:
        oeth_mav_source = PriceAggregator(
            algorithm="median",
            sources=[
                MaverickV2PriceSource(asset="oeth", currency="eth"),
            ],
        )

        oeth_mav_price = await oeth_mav_source.fetch_new_datapoint()
        if oeth_mav_price is None:
            logger.error("Unable to get price from MaverickV2.")
            return None, None
        print(oeth_mav_price)
        return oeth_mav_price

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:

        asset = asset.lower()
        currency = currency.lower()
        oeth_price, timestamp = await self.get_oeth_usd()
        eth_price, timestamp = await self.get_eth_usd()
        mav_price, timestamp = await self.get_oeth_eth_mav()
        if oeth_price and eth_price and mav_price is not None:
            return ((oeth_price / eth_price) + mav_price) / 2, timestamp
        else:
            logger.error("Unable to calculate OETH/ETH (please check sources).")
            return None, None


@dataclass
class oethEthSource(PriceSource):
    asset: str = ""
    currency: str = ""
    sources: str = ""
    service: oethEthService = field(default_factory=oethEthService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = oethEthSource(asset="oeth", currency="eth")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
