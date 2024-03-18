from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional

from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class sFRAXSpotPriceService(WebPriceService):
    """Custom sFRAX Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom sFRAX Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_sfrax_usd_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get sfrax_eth_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get sfrax_eth_ratio")
            return None
        w3 = ep.web3
        # get ratio
        sfrax_eth_ratio_bytes = w3.eth.call(
            {
                "to": "0xA663B02CF0a4b149d2aD41910CB81e23e1c41c32",
                "data": "0x99530b06",
            }
        )
        sfrax_usd_ratio_decoded = w3.toInt(sfrax_eth_ratio_bytes)
        sfrax_usd_ratio = w3.fromWei(sfrax_usd_ratio_decoded, "ether")
        print(f"Ratio from sFRAX contract: {sfrax_usd_ratio}")
        return float(sfrax_usd_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of USDM from multiple sources and
        calculates the price of sFRAX using the ratio of sFRAX to FRAX from sFRAX contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        sfrax_ratio = self.get_sfrax_usd_ratio()
        if sfrax_ratio is None:
            logger.error("Unable to get sfrax_USDM_ratio")
            return None, None

        source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="frax", currency="usd"),
                CurveFiUSDPriceSource(asset="frax", currency="usd"),
                CoinpaprikaSpotPriceSource(asset="frax-frax", currency=currency),
                UniswapV3PriceSource(asset="frax", currency=currency),
            ],
        )

        sfrax_price, timestamp = await source.fetch_new_datapoint()
        if sfrax_price is None:
            logger.error("Unable to get sfrax price")
            return None, None
        return sfrax_price * sfrax_ratio, timestamp


@dataclass
class sFRAXSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: sFRAXSpotPriceService = field(default_factory=sFRAXSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = sFRAXSpotPriceSource(asset="sFRAX", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
