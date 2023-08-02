from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional

from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

MAVERICK_CONTRACT = "0x9980ce3b5570e41324904f46A06cE7B466925E23"
SWETH_CONTRACT = "0xf951E335afb289353dc249e82926178EaC7DEd78"


class swETHSpotPriceService(WebPriceService):
    """Custom swETH Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom swETH Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()
        self.contract: Optional[str] = None
        self.calldata: Optional[str] = None

    def get_sweth_eth_ratio(self) -> Optional[float]:
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=1)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get sweth_eth_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get sweth_eth_ratio")
            return None
        w3 = ep._web3
        if w3 is None:
            logger.error("Unable to get web3 for mainnet to get sweth_eth_ratio")
            return None
        # get ratio
        sweth_eth_ratio_bytes = w3.eth.call({"to": self.contract, "data": self.calldata})

        sweth_eth_ratio_decoded = w3.toInt(sweth_eth_ratio_bytes)
        sweth_eth_ratio = w3.fromWei(sweth_eth_ratio_decoded, "ether")
        # Maverick AMM uses square root of ratio
        if self.contract == MAVERICK_CONTRACT:
            sweth_eth_ratio = sweth_eth_ratio**2
        logger.debug(f"sweth_eth_ratio: {sweth_eth_ratio}")
        return float(sweth_eth_ratio)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the median price of eth in usd and
        converts the sweth/eth ratio to get sweth/usd price
        """
        asset = asset.lower()
        currency = currency.lower()

        sweth_eth_ratio = self.get_sweth_eth_ratio()
        if asset == "sweth" and currency == "eth":
            return sweth_eth_ratio, datetime_now_utc()

        if sweth_eth_ratio is None:
            logger.error("Unable to get sweth_eth_ratio")
            return None, None

        source = eth_usd_median_feed.source

        eth_price, timestamp = await source.fetch_new_datapoint()
        if eth_price is None:
            logger.error("Unable to get eth/usd price")
            return None, None
        return sweth_eth_ratio * eth_price, timestamp


@dataclass
class swETHSpotPriceSource(PriceSource):
    """Gets data from swETH contract"""

    asset: str = ""
    currency: str = ""
    service: swETHSpotPriceService = field(default_factory=swETHSpotPriceService, init=False)

    def __post_init__(self) -> None:
        self.service.contract = SWETH_CONTRACT
        self.service.calldata = "0xd68b2cb6"


@dataclass
class swETHMaverickSpotPriceSource(PriceSource):
    """Gets data from Maverick AMM"""

    asset: str = ""
    currency: str = ""
    service: swETHSpotPriceService = field(default_factory=swETHSpotPriceService)

    def __post_init__(self) -> None:
        self.service.contract = MAVERICK_CONTRACT
        self.service.calldata = "0x91c0914e000000000000000000000000817e8c9a99db98082ca187e4f80498586bf6bc1b"
