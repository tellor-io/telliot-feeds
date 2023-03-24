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
from telliot_feeds.sources.price.spot.curvefi import CurveFinanceSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)


class WstETHSpotPriceService(WebPriceService):
    """Custom WstETH Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom WstETH Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def get_wsteth_steth_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get wsteth_eth_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get wsteth_eth_ratio")
            return None
        w3 = ep.web3
        # get ratio
        wsteth_eth_ratio_bytes = w3.eth.call(
            {
                "to": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
                "data": "0xbb2952fc0000000000000000000000000000000000000000000000000de0b6b3a7640000",
            }
        )
        wsteth_eth_ratio_decoded = w3.toInt(wsteth_eth_ratio_bytes)
        wsteth_eth_ratio = w3.fromWei(wsteth_eth_ratio_decoded, "ether")
        return float(wsteth_eth_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price of stETH from multiple sources and
        calculates the price of wstETH using the ratio of wstETH to stETH from wstETH contract.
        """
        asset = asset.lower()
        currency = currency.lower()

        wsteth_ratio = self.get_wsteth_steth_ratio()
        if wsteth_ratio is None:
            logger.error("Unable to get wsteth_eth_ratio")
            return None, None

        source = PriceAggregator(
            algorithm="median",
            sources=[
                CoinGeckoSpotPriceSource(asset="steth", currency=currency),
                CoinpaprikaSpotPriceSource(asset="steth-lido-staked-ether", currency=currency),
                UniswapV3PriceSource(asset="steth", currency=currency),
                CurveFinanceSpotPriceSource(asset="steth", currency=currency),
            ],
        )

        steth_price, timestamp = await source.fetch_new_datapoint()
        if steth_price is None:
            logger.error("Unable to get steth price")
            return None, None
        return steth_price * wsteth_ratio, timestamp


@dataclass
class WstETHSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: WstETHSpotPriceService = field(default_factory=WstETHSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = WstETHSpotPriceSource(asset="wsteth", currency="eth")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
