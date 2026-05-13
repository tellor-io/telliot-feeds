from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from typing import Any

import requests

from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

OSMOSIS_LCD_URL = "https://lcd.osmosis.zone"

# stATOM/ATOM concentrated liquidity pool on Osmosis (pool 1283)
STATOM_ATOM_POOL_ID = 1283

STATOM_IBC = "ibc/C140AFD542AE77BD7DCC83F13FDD8C5E5BB8C4929785E6EC2F4C636F98F17901"
ATOM_IBC = "ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2"


class OsmosisPoolPriceService(WebPriceService):
    """Osmosis Concentrated Liquidity Pool Price Service for stATOM/USD.

    Fetches the current_sqrt_price from the Osmosis LCD REST API for the
    stATOM/ATOM pool, squares it to obtain the stATOM/ATOM ratio, then
    multiplies by the ATOM/USD price from CoinGecko.

    Only supports asset="statom", currency="usd".
    """

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Osmosis Pool Price Service"
        kwargs["url"] = OSMOSIS_LCD_URL
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        asset = asset.lower()
        currency = currency.lower()

        if asset != "statom" or currency != "usd":
            logger.error(f"OsmosisPoolPriceService only supports statom/usd, got {asset}/{currency}")
            return None, None

        pool_url = f"{self.url}/osmosis/gamm/v1beta1/pools/{STATOM_ATOM_POOL_ID}"

        try:
            with requests.Session() as s:
                r = s.get(pool_url, timeout=self.timeout)
                if r.status_code != 200:
                    logger.warning(f"Osmosis LCD returned status {r.status_code} for pool {STATOM_ATOM_POOL_ID}")
                    return None, None
                data = r.json()
        except requests.exceptions.ConnectTimeout:
            logger.warning("Osmosis LCD request timed out")
            return None, None
        except Exception as e:
            logger.warning(f"Osmosis LCD request failed: {e}")
            return None, None

        pool = data.get("pool")
        if pool is None:
            logger.warning("Osmosis pool response missing 'pool' field")
            return None, None

        # Validate that this pool contains stATOM and ATOM
        pool_tokens: list = pool.get("pool_liquidity", []) or pool.get("tokens", [])
        # CL pools expose tokens via token0/token1 or pool_assets; try all known fields
        token_denoms: set = set()
        for key in ("token0", "token1"):
            val = pool.get(key)
            if val:
                token_denoms.add(val)
        for asset_entry in pool.get("pool_assets", []):
            coin = asset_entry.get("token", {})
            if coin.get("denom"):
                token_denoms.add(coin["denom"])
        for entry in pool_tokens:
            if isinstance(entry, dict) and entry.get("denom"):
                token_denoms.add(entry["denom"])

        if not ({STATOM_IBC, ATOM_IBC} <= token_denoms):
            logger.error(
                f"Pool {STATOM_ATOM_POOL_ID} does not contain the expected stATOM/ATOM tokens. "
                f"Found denoms: {token_denoms}"
            )
            return None, None

        # Extract current_sqrt_price and square it to get stATOM/ATOM
        sqrt_price_str = pool.get("current_sqrt_price")
        if sqrt_price_str is None:
            logger.warning("Osmosis pool response missing 'current_sqrt_price'")
            return None, None

        try:
            sqrt_price = float(sqrt_price_str)
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not parse current_sqrt_price '{sqrt_price_str}': {e}")
            return None, None

        statom_atom_ratio = sqrt_price**2

        # Determine timestamp from pool's last_liquidity_update
        timestamp: Any = None
        last_update_str = pool.get("last_liquidity_update")
        if last_update_str:
            try:
                # Osmosis returns RFC3339 strings like "2024-01-15T12:34:56.789Z"
                ts = last_update_str.rstrip("Z")
                if "." in ts:
                    ts_dt = datetime.strptime(ts[:26], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
                else:
                    ts_dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                timestamp = ts_dt
            except Exception as e:
                logger.warning(f"Could not parse last_liquidity_update '{last_update_str}': {e}")

        # Fetch ATOM/USD price from CoinGecko
        atom_usd_source = CoinGeckoSpotPriceSource(asset="atom", currency="usd")
        atom_price, atom_ts = await atom_usd_source.fetch_new_datapoint()
        if atom_price is None:
            logger.error("Could not retrieve ATOM/USD price from CoinGecko")
            return None, None

        statom_usd = statom_atom_ratio * atom_price
        logger.info(
            f"Osmosis stATOM/USD: sqrt_price={sqrt_price}, ratio={statom_atom_ratio:.6f}, "
            f"ATOM/USD={atom_price}, stATOM/USD={statom_usd:.6f}"
        )

        # Use the pool's own timestamp if available, otherwise fall back to now
        if timestamp is None:
            from telliot_feeds.dtypes.datapoint import datetime_now_utc

            timestamp = datetime_now_utc()

        return statom_usd, timestamp


@dataclass
class OsmosisPoolPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: OsmosisPoolPriceService = field(default_factory=OsmosisPoolPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = OsmosisPoolPriceSource(asset="statom", currency="usd")
        price, ts = await source.fetch_new_datapoint()
        print(f"stATOM/USD = {price} @ {ts}")

    asyncio.run(main())
