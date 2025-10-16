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


class vyUSDSpotPriceService(WebPriceService):
    """Custom vyUSD Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom vyUSD Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_vyusd_usdc_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get vyusd_eth_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get vyusd_eth_ratio")
            return None
        w3 = ep.web3
        # get ratio exchangeRate
        vyusd_ratio_bytes = w3.eth.call(
            {
                "to": "0x2e3C5e514EEf46727DE1FE44618027A9b70D92FC",
                "data": "0xd14f3da1",
            }
        )
        vyusd_usd_ratio_decoded = w3.to_int(vyusd_ratio_bytes)
        vyusd_usd_ratio = w3.from_wei(vyusd_usd_ratio_decoded, "ether")
        print(f"Ratio from vyUSD contract: {vyusd_usd_ratio}")
        return float(vyusd_usd_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of USDM from multiple sources and
        calculates the price of vyUSD using the ratio of vyUSD to FRAX from vyUSD contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        vyusd_ratio = self.get_vyusd_usdc_ratio()
        if vyusd_ratio is None:
            logger.error("Unable to get vyusd_USDM_ratio")
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

        vyusd_price, timestamp = await source.fetch_new_datapoint()
        if vyusd_price is None:
            logger.error("Unable to get vyusd price")
            return None, None
        return vyusd_price * vyusd_ratio, timestamp


@dataclass
class vyUSDSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: vyUSDSpotPriceService = field(default_factory=vyUSDSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = vyUSDSpotPriceSource(asset="vyUSD", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
