from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional

from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class yETHSpotPriceService(WebPriceService):
    """Custom yETH Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom yETH Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_yeth_eth_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get yeth_eth_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get yeth_eth_ratio")
            return None
        w3 = ep.web3
        # get ratio exchangeRate
        yeth_ratio_bytes = w3.eth.call(
            {
                "to": "0x8464F6eCAe1EA58E816C13f964030eAb8Ec123A",
                "data": "0x3ba0b9a9",
            }
        )
        yeth_eth_ratio_decoded = w3.to_int(yeth_ratio_bytes)
        yeth_eth_ratio = w3.from_wei(yeth_eth_ratio_decoded, "ether")
        print(f"Ratio from yeth contract: {yeth_eth_ratio}")
        return float(yeth_eth_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of ETH from multiple sources and
        calculates the price of yeth using the ratio of yeth to ETH from yeth contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        yeth_ratio = self.get_yeth_eth_ratio()
        if yeth_ratio is None:
            logger.error("Unable to get yeth_eth_ratio")
            return None, None

        source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="eth", currency="usd"),
                GeminiSpotPriceSource(asset="eth", currency="usd"),
                KrakenSpotPriceSource(asset="eth", currency="usd"),
                OKXSpotPriceSource(asset="eth", currency="usdt"),
            ],
        )

        eth_price, timestamp = await source.fetch_new_datapoint()
        if eth_price is None:
            logger.error("Unable to get eth price")
            return None, None
        return eth_price * yeth_ratio, timestamp


@dataclass
class yETHSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: yETHSpotPriceService = field(default_factory=yETHSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = yETHSpotPriceSource(asset="yeth", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
