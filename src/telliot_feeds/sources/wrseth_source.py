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


class wrsETHSpotPriceService(WebPriceService):
    """Custom wrsETH Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom wrsETH Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_wrseth_eth_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=34443)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get wrseth_eth_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get wrseth_eth_ratio")
            return None
        w3 = ep.web3
        # get ratio
        wrseth_eth_ratio_bytes = w3.eth.call(
            {
                "to": "0xbDf612E616432AA8e8D7d8cC1A9c934025371c5C",
                "data": "0x679aefce",
            }
        )
        wrseth_eth_ratio_decoded = w3.toInt(wrseth_eth_ratio_bytes)
        wrseth_eth_ratio = w3.fromWei(wrseth_eth_ratio_decoded, "ether")
        print(f"Ratio from wrseth contract: {wrseth_eth_ratio}")
        return float(wrseth_eth_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of wrsETH from multiple sources and
        calculates the price of wrseth using the ratio of wrsETH to rsETH from wrsETH contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        wrseth_ratio = self.get_wrseth_eth_ratio()
        if wrseth_ratio is None:
            logger.error("Unable to get wrsETH to rsETH ratio")
            return None, None

        source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="rseth", currency="usd"),
                CurveFiUSDPriceSource(asset="rseth", currency="usd"),
                CoinpaprikaSpotPriceSource(asset="rseth-rseth", currency=currency),
                UniswapV3PriceSource(asset="rseth", currency=currency),
            ],
        )

        wrseth_price, timestamp = await source.fetch_new_datapoint()
        if wrseth_price is None:
            logger.error("Unable to get wrseth price")
            return None, None
        return wrseth_price * wrseth_ratio, timestamp


@dataclass
class wrsETHSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: wrsETHSpotPriceService = field(default_factory=wrsETHSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = wrsETHSpotPriceSource(asset="wrseth", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
