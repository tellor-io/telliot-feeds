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
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class sfrxUSDSpotPriceService(WebPriceService):
    """Custom sfrxUSD Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom sfrxUSD Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_sfrxusd_frxusd_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get sfrxusd_frxusd_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get sfrxusd_frxusd_ratio")
            return None
        w3 = ep.web3
        # get supply numbers from sfrxUSD contract
        sfrxusd_totalAssets_bytes = w3.eth.call(
            {
                "to": "0xcf62F905562626CfcDD2261162a51fd02Fc9c5b6",
                "data": "0x01e1d114",
            }
        )
        sfrxusd_totalSupply_bytes = w3.eth.call(
            {
                "to": "0xcf62F905562626CfcDD2261162a51fd02Fc9c5b6",
                "data": "0x18160ddd",
            }
        )
        sfrxusd_totalAssets_decoded = w3.to_int(sfrxusd_totalAssets_bytes)
        sfrxusd_totalSupply_decoded = w3.to_int(sfrxusd_totalSupply_bytes)
        sfrxusd_frxusd_ratio = sfrxusd_totalAssets_decoded / sfrxusd_totalSupply_decoded
        logger.info(f"sfrxusd/frxusd Ratio from contract: {sfrxusd_frxusd_ratio}")
        return float(sfrxusd_frxusd_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of USDM from multiple sources and
        calculates the price of sfrxUSD using the ratio of sFRXUSD to FRXUSD from sFRXUSD contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        sfrxusd_frxusd_ratio = self.get_sfrxusd_frxusd_ratio()
        if sfrxusd_frxusd_ratio is None:
            logger.error("Unable to get sfrxusd_frxusd_ratio")
            return None, None

        source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="frxusd", currency="usd"),
                CurveFiUSDPriceSource(asset="frxusd", currency="usd"),
                CoinpaprikaSpotPriceSource(asset="frxusd-frax-usd", currency="usd"),
            ],
        )
        frxusd_price, timestamp = await source.fetch_new_datapoint()
        if frxusd_price is None:
            logger.error("Unable to get frxusd price")
            return None, None
        return frxusd_price * sfrxusd_frxusd_ratio, timestamp


@dataclass
class sfrxUSDSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: sfrxUSDSpotPriceService = field(default_factory=sfrxUSDSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = sfrxUSDSpotPriceSource(asset="sfrxusd", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
