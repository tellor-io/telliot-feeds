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
from telliot_feeds.sources.price.spot.curvefiprice import CurveFiUSDPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

SUSDE_CONTRACT = "0x9D39A5DE30e57443BfF2A8307A4256c8797A3497"


class sUSDESpotPriceService(WebPriceService):
    """Custom sUSDe Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom sUSDe Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_susde_usde_ratio(self) -> Optional[float]:
        """Read totalAssets / totalSupply from the sUSDe ERC4626 vault to get the sUSDe/USDe ratio."""
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get susde_usde_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get susde_usde_ratio")
            return None
        w3: Web3 = ep.web3

        total_assets_bytes = w3.eth.call(
            {
                "to": SUSDE_CONTRACT,
                "data": HexStr("0x01e1d114"),  # totalAssets()
            }
        )
        total_supply_bytes = w3.eth.call(
            {
                "to": SUSDE_CONTRACT,
                "data": HexStr("0x18160ddd"),  # totalSupply()
            }
        )

        total_assets = w3.to_int(total_assets_bytes)
        total_supply = w3.to_int(total_supply_bytes)
        ratio = total_assets / total_supply
        logger.info(f"sUSDe/USDe ratio from contract: {ratio}")
        return float(ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Get the sUSDe/USD price by multiplying the USDe/USD median price by the sUSDe/USDe ratio."""
        asset = asset.lower()
        currency = currency.lower()

        susde_usde_ratio = self.get_susde_usde_ratio()
        if susde_usde_ratio is None:
            logger.error("Unable to get sUSDe/USDe ratio")
            return None, None

        usde_usd_source = PriceAggregator(
            algorithm="median",
            sources=[
                CurveFiUSDPriceSource(asset="usde", currency="usd"),
                CoinGeckoSpotPriceSource(asset="usde", currency="usd"),
                CoinpaprikaSpotPriceSource(asset="usde-ethena-usde", currency="usd"),
            ],
        )

        usde_price, timestamp = await usde_usd_source.fetch_new_datapoint()
        if usde_price is None:
            logger.error("Unable to get USDe/USD price")
            return None, None

        return usde_price * susde_usde_ratio, timestamp


@dataclass
class sUSDESpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: sUSDESpotPriceService = field(default_factory=sUSDESpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = sUSDESpotPriceSource(asset="susde", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
