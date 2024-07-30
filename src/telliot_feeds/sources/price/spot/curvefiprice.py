from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


ethereum_contract_map = {
    "sdai": "0x83F20F44975D03b1b09e64809B757c47f942BEeA",
    "sfrax": "0xA663B02CF0a4b149d2aD41910CB81e23e1c41c32",
    "eth": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
    "steth": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
    "btc": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "frax": "0x853d955acef822db058eb8505911ed77f175b99e",
    "frxeth": "0x5e8422345238f34275888049021821e8e08caa1f",
    "ezeth": "0xbf5495efe5db9ce00f80364c8b423567e58d2110",
    "weeth": "0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee",
    "rseth": "0xa1290d69c65a6fe4df752f95823fae25cb99e5a7",
    "ousd": "0x2a8e1e676ec238d8a992307b495b45b3feaa5e86",
}


class CurveFiUSDPriceService(WebPriceService):
    """CurveFinance Curve-Prices Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Curve-Prices Service"
        kwargs["url"] = "https://prices.curve.fi/v1/usd_price"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price from the Curve finance API."""
        asset = asset.lower()
        currency = currency.lower()
        if asset not in ethereum_contract_map:
            logger.error(f"Asset not mapped for curve price Source: {asset}")
            return None, None
        asset_address = ethereum_contract_map[asset]

        if currency != "usd":
            logger.error("Service for usd pairs only")
            return None, None

        request_url = f"/ethereum/{asset_address}"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None

        response = d.get("response")
        if response is None:
            logger.error("Error parsing Curve Finance API response, 'response' key not found")
            return None, None

        data = response.get("data")
        if data is None:
            logger.error("Error parsing Curve Finance API response 'data' key not found")
            return None, None

        asset_price = data.get("usd_price")
        if asset_price is None:
            logger.error("Failed to parse response data from Curve Finance API 'usd_price' key not found")
            return None, None

        isAddress = data.get("address", "").lower() == asset_address.lower()

        if not isAddress:
            logger.error("Asset '0x' address in API response doesn't match contract address stored")
            return None, None
        return asset_price, datetime_now_utc()


@dataclass
class CurveFiUSDPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: CurveFiUSDPriceService = field(default_factory=CurveFiUSDPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = CurveFiUSDPriceSource(asset="frxeth", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
