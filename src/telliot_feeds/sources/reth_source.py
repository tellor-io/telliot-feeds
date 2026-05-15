from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional

from telliot_core.apps.telliot_config import TelliotConfig
from web3 import Web3

from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

RETH_CONTRACT = Web3.to_checksum_address("0xae78736cd615f374d3085123a210448e74fc6393")
GET_EXCHANGE_RATE_CALLDATA = "0xe6aa216c"


class RethSpotPriceService(WebPriceService):
    """Custom rETH Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom rETH Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_reth_eth_ratio(self) -> Optional[float]:
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get reth_eth_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get reth_eth_ratio")
            return None
        w3 = ep.web3
        reth_eth_ratio_bytes = w3.eth.call({"to": RETH_CONTRACT, "data": GET_EXCHANGE_RATE_CALLDATA})
        reth_eth_ratio_decoded = w3.to_int(reth_eth_ratio_bytes)
        reth_eth_ratio = w3.from_wei(reth_eth_ratio_decoded, "ether")
        reth_eth_ratio_float = float(reth_eth_ratio)
        logger.info(f"rETH/ETH ratio from contract: {reth_eth_ratio_float}")
        return reth_eth_ratio_float

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Gets the median ETH/USD price and multiplies by the rETH exchange rate from contract."""
        asset = asset.lower()
        currency = currency.lower()

        reth_ratio = self.get_reth_eth_ratio()
        if reth_ratio is None:
            logger.error("Unable to get reth_eth_ratio")
            return None, None

        source = eth_usd_median_feed.source

        eth_price, timestamp = await source.fetch_new_datapoint()
        if eth_price is None:
            logger.error("Unable to get eth/usd price")
            return None, None
        return reth_ratio * eth_price, timestamp


@dataclass
class RethSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: RethSpotPriceService = field(default_factory=RethSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = RethSpotPriceSource(asset="reth", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
