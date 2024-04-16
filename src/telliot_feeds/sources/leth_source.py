from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional

from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class LETHSpotPriceService(WebPriceService):
    """Custom LETH Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom LETH Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_leth_usd_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get leth_eth_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get leth_eth_ratio")
            return None
        w3 = ep.web3
        # get ratio
        leth_eth_ratio_bytes = w3.eth.call(
            {
                "to": "0xE7895ed01a1a6AAcF1c2E955aF14E7cf612E7F9d",
                "data": "",
            }
        )
        leth_usd_ratio_decoded = w3.toInt(leth_eth_ratio_bytes)
        leth_usd_ratio = w3.fromWei(leth_usd_ratio_decoded, "ether")
        print(f"Ratio from LETH contract: {leth_usd_ratio}")
        return float(leth_usd_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of ETH from multiple sources and
        calculates the price of LETH using the ratio of LETH to ETH from LETH contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        leth_ratio = self.get_leth_usd_ratio()
        if leth_ratio is None:
            logger.error("Unable to get leth_eth_ratio")
            return None, None

        source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="eth", currency="usd"),
                CoinbaseSpotPriceSource(asset="eth", currency="usd"),
                GeminiSpotPriceSource(asset="eth", currency="usd"),
                KrakenSpotPriceSource(asset="eth", currency="usd"),
            ],
        )

        leth_price, timestamp = await source.fetch_new_datapoint()
        if leth_price is None:
            logger.error("Unable to get LETH price")
            return None, None
        return leth_price * leth_ratio, timestamp


@dataclass
class LETHSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: LETHSpotPriceService = field(default_factory=LETHSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = LETHSpotPriceSource(asset="leth", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
