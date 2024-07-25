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
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class wUSDMSpotPriceService(WebPriceService):
    """Custom wUSDM Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom wUSDM Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_wusdm_usd_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get wusdm_eth_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get wusdm_eth_ratio")
            return None
        w3 = ep.web3
        # get ratio
        wusdm_eth_ratio_bytes = w3.eth.call(
            {
                "to": "0x57F5E098CaD7A3D1Eed53991D4d66C45C9AF7812",
                "data": "0x07a2d13a0000000000000000000000000000000000000000000000000de0b6b3a7640000",
            }
        )
        wusdm_usd_ratio_decoded = w3.toInt(wusdm_eth_ratio_bytes)
        wusdm_usd_ratio = w3.fromWei(wusdm_usd_ratio_decoded, "ether")
        print(f"Ratio from wUSDM contract: {wusdm_usd_ratio}")
        return float(wusdm_usd_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of USDM from multiple sources and
        calculates the price of wUSDM using the ratio of wUSDM to USDMfrom wUSDM contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        wusdm_ratio = self.get_wusdm_usd_ratio()
        if wusdm_ratio is None:
            logger.error("Unable to get wUSDM_USDM_ratio")
            return None, None

        source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="usdm", currency="usd"),
                CoinpaprikaSpotPriceSource(asset="usdm-mountain-protocol-usd", currency=currency),
            ],
        )

        wusdm_price, timestamp = await source.fetch_new_datapoint()
        if wusdm_price is None:
            logger.error("Unable to get wusdm price")
            return None, None
        return wusdm_price * wusdm_ratio, timestamp


@dataclass
class wUSDMSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: wUSDMSpotPriceService = field(default_factory=wUSDMSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = wUSDMSpotPriceSource(asset="wusdm", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
