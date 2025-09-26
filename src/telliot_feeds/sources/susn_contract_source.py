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
from telliot_feeds.sources.price.spot.coinpaprika import CoinpaprikaSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class sUSNSpotPriceService(WebPriceService):
    """Custom sUSN Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom sUSN Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_susn_usd_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get susn_eth_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get susn_eth_ratio")
            return None
        w3: Web3 = ep.web3
        # get ratio
        susn_total_assets_bytes = w3.eth.call(
            {
                "to": "0xE24a3DC889621612422A64E6388927901608B91D",
                "data": HexStr("0x01e1d114"),
            }
        )
        susn_total_supply_bytes = w3.eth.call(
            {
                "to": "0xE24a3DC889621612422A64E6388927901608B91D",
                "data": HexStr("0x18160ddd"),
            }
        )

        susn_total_assets_decoded = w3.to_int(susn_total_assets_bytes)
        susn_total_supply_decoded = w3.to_int(susn_total_supply_bytes)
        susn_usd_ratio = susn_total_assets_decoded / susn_total_supply_decoded
        logger.info(f"Ratio from sUSN contract: {susn_usd_ratio}")
        return float(susn_usd_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of sUSN from multiple sources and
        calculates the price of sUSN using the ratio of sUSN to USNfrom sUSN contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        susn_ratio = self.get_susn_usd_ratio()
        if susn_ratio is None:
            logger.error("Unable to get sUSN_USN_ratio")
            return None, None

        source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="usn", currency="usd"),
                CoinpaprikaSpotPriceSource(asset="usn1-noon-usn", currency="usd"),
            ],
        )

        susn_price, timestamp = await source.fetch_new_datapoint()
        if susn_price is None:
            logger.error("Unable to get susn price")
            return None, None
        return susn_price * susn_ratio, timestamp


@dataclass
class sUSNSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: sUSNSpotPriceService = field(default_factory=sUSNSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = sUSNSpotPriceSource(asset="susn", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
