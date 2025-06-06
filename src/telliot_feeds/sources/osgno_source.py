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
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class osGNOSpotPriceService(WebPriceService):
    """Custom osGNO Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom osGNO Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_osgno_gno_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=100)
        if not endpoint:
            logger.error("Endpoint not found for gnosis to get osgno_gno_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get osgno_gno_ratio")
            return None
        w3 = ep.web3
        # get ratio
        osgno_gno_ratio_bytes = w3.eth.call(
            {
                "to": "0x9B1b13afA6a57e54C03AD0428a4766C39707D272",
                "data": "0x679aefce",
            }
        )
        osgno_gno_ratio_decoded = w3.to_int(osgno_gno_ratio_bytes)
        osgno_gno_ratio = w3.from_wei(osgno_gno_ratio_decoded, "ether")
        print(f"osgno_gno_ratio: {osgno_gno_ratio}")
        return float(osgno_gno_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of GNO from multiple sources and
        calculates the price of osGNO using the ratio of osGNO to GNO from osGNO contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        osgno_ratio = self.get_osgno_gno_ratio()
        if osgno_ratio is None:
            logger.error("Unable to get osgno_gno_ratio")
            return None, None

        source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="gno", currency="usd"),
                KrakenSpotPriceSource(asset="gno", currency="usd"),
                CoinpaprikaSpotPriceSource(asset="gno-gnosis", currency="usd"),
            ],
        )

        gno_price, timestamp = await source.fetch_new_datapoint()
        if gno_price is None:
            logger.error("Unable to get gno price")
            return None, None
        return gno_price * osgno_ratio, timestamp


@dataclass
class osGNOSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: osGNOSpotPriceService = field(default_factory=osGNOSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = osGNOSpotPriceSource(asset="osgno", currency="eth")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
