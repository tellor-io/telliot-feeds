from dataclasses import dataclass
from dataclasses import field
from typing import Any

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


contract_map = {
    "eth": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
    "steth": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
    "btc": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "sfrax": "0xe3b3FE7bcA19cA77Ad877A5Bebab186bEcfAD906",
}


class CurveFinanceSpotPriceService(WebPriceService):
    """CurveFinance Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "CurveFinance Price Service"
        kwargs["url"] = "https://api.curve.fi"
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the price from the Curve finance API."""
        asset = asset.lower()
        currency = currency.lower()
        if asset not in contract_map:
            logger.error(f"Asset not supported: {asset}")
            return None, None
        asset_address = contract_map[asset]

        request_url = "/api/getPools/ethereum/main"

        d = self.get_url(request_url)

        if "error" in d:
            logger.error(d)
            return None, None
        elif "response" in d:
            response = d["response"]
            data = response.get("data")

            if data is None:
                logger.error("No data in returned response")
                return None, None
            pool_data = data.get("poolData")
            if pool_data is None:
                logger.error("Failed to parse response data from Curve Finance API")
                return None, None
            asset_price = None
            for pool in pool_data:
                for coin in pool["coins"]:
                    if coin["address"] == asset_address:
                        asset_price = coin.get("usdPrice")
                        break
                if asset_price is not None:
                    break

            if asset_price is None:
                logger.error(f"Unable to find price for {asset} from Curve Finance API")
                return None, None
            if currency == "usd":
                return asset_price, datetime_now_utc()
            else:
                currency_price = None
                for pool in pool_data:
                    for coin in pool["coins"]:
                        if coin["address"] == contract_map[currency]:
                            currency_price = coin.get("usdPrice")
                            break
                    if currency_price is not None:
                        break
                if currency_price is None:
                    logger.error(f"Unable to find price for {currency} from Curve Finance API")
                    return None, None
                return asset_price / currency_price, datetime_now_utc()

        else:
            raise Exception("Invalid response from get_url")


@dataclass
class CurveFinanceSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: CurveFinanceSpotPriceService = field(default_factory=CurveFinanceSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = CurveFinanceSpotPriceSource(asset="steth", currency="btc")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
