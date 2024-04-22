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

    def get_leth_eth_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=324)
        if not endpoint:
            logger.error("Endpoint not found for network 324 (for LETH feed?)")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint to get leth_eth_ratio")
            return None
        w3 = ep.web3

        # get total pooled tokens from LETH contract
        try:
            total_pooled_tokens_bytes = w3.eth.call(
                {
                    "to": "0xE7895ed01a1a6AAcF1c2E955aF14E7cf612E7F9d",
                    "data": "0xb6f81c85",
                }
            )
            total_pooled_tokens_decoded = w3.toInt(total_pooled_tokens_bytes)
            total_pooled_tokens = w3.fromWei(total_pooled_tokens_decoded, "ether")
            if total_pooled_tokens == 0:
                logger.error("LETH contract response is 0!")
                return None
            else:
                logger.info(f"total pooled tokens (leth contract 0xE78...): {total_pooled_tokens}")

        except Exception as e:
            logger.error(f"Could not read total pooled LETH from contract!: {e}")
            return None

        # get total Supply from LETH contract
        try:
            total_supply_bytes = w3.eth.call(
                {
                    "to": "0xE7895ed01a1a6AAcF1c2E955aF14E7cf612E7F9d",
                    "data": "0x18160ddd",
                }
            )
            total_supply_decoded = w3.toInt(total_supply_bytes)
            total_supply = w3.fromWei(total_supply_decoded, "ether")
            if total_supply == 0:
                logger.error("leth contract response is 0 for supply!")
                return None
            else:
                logger.info(f"total supply (leth contract 0xE78...): {total_pooled_tokens}")

        except Exception as e:
            logger.error(f"Could not read supply of leth from contract!: {e}")
            return None

        leth_eth_ratio = format((total_pooled_tokens / total_supply), ".18f")
        logger.info(f"leth / eth ratio = {leth_eth_ratio}")
        return float(leth_eth_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of ETH from multiple sources and
        calculates the price of LETH using the ratio of LETH to ETH from LETH contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        leth_ratio = self.get_leth_eth_ratio()
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
