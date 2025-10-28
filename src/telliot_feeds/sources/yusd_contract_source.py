from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional

from eth_typing import HexStr
from telliot_core.apps.telliot_config import TelliotConfig
from web3 import Web3

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


class yUSDSpotPriceService(WebPriceService):
    """Custom yUSD Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom yUSD Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_yusd_usdc_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get yusd_usdc_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get yusd_usdc_ratio")
            return None
        w3: Web3 = ep.web3
        # get ratio
        yusd_exchange_rate_bytes = w3.eth.call(
            {
                "to": "0x19Ebd191f7A24ECE672ba13A302212b5eF7F35cb",
                "data": HexStr("0x3ba0b9a9"),
            }
        )
        yusd_exchange_rate_decoded = w3.to_int(yusd_exchange_rate_bytes)
        yusd_exchange_rate = w3.from_wei(yusd_exchange_rate_decoded, "mwei")
        logger.info(f"Ratio from yUSD contract: {yusd_exchange_rate}")
        return float(yusd_exchange_rate)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of sUSN from multiple sources and
        calculates the price of yUSD using the ratio of yUSD to USDC from yUSD contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        yusd_exchange_rate = self.get_yusd_usdc_ratio()
        if yusd_exchange_rate is None:
            logger.error("Unable to get yUSD_USDC_ratio")
            return None, None

        source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="usdc", currency="usd"),
                GeminiSpotPriceSource(asset="usdc", currency="usd"),
                KrakenSpotPriceSource(asset="usdc", currency="usd"),
                OKXSpotPriceSource(asset="usdc", currency="usdt"),
            ],
        )

        yusd_price, timestamp = await source.fetch_new_datapoint()
        if yusd_price is None:
            logger.error("Unable to get yusd price")
            return None, None
        return yusd_price * yusd_exchange_rate, timestamp


@dataclass
class yUSDSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: yUSDSpotPriceService = field(default_factory=yUSDSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = yUSDSpotPriceSource(asset="yusd", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
