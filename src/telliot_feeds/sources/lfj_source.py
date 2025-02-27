from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import List
from typing import Optional

from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

LFJ_QUOTER_CONTRACT = "0x9A550a522BBaDFB69019b0432800Ed17855A51C3"
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "address[]", "name": "route", "type": "address[]"},
            {"internalType": "uint128", "name": "amountIn", "type": "uint128"},
        ],
        "name": "findBestPathFromAmountIn",
        "outputs": [
            {
                "components": [
                    {"internalType": "address[]", "name": "route", "type": "address[]"},
                    {"internalType": "address[]", "name": "pairs", "type": "address[]"},
                    {"internalType": "uint256[]", "name": "binSteps", "type": "uint256[]"},
                    {"internalType": "uint8[]", "name": "versions", "type": "uint8[]"},  # Enum is uint8
                    {"internalType": "uint128[]", "name": "amounts", "type": "uint128[]"},
                    {"internalType": "uint128[]", "name": "virtualAmountsWithoutSlippage", "type": "uint128[]"},
                    {"internalType": "uint128[]", "name": "fees", "type": "uint128[]"},
                ],
                "internalType": "tuple",  # Struct is tuple in ABI
                "name": "quote",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    }
]
SOLVBTC_ROUTE = [
    "0xbc78D84Ba0c46dFe32cf2895a19939c86b81a777",  # solvBTC
    "0x152b9d0FdC40C096757F570A51E494bd4b943E50",  # BTC.b
    "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",  # AVAX
    "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",  # USDC
]

SOLVBTCBBN_ROUTE = [
    "0xCC0966D8418d412c599A6421b760a847eB169A8c",  # solvBTC.bbn
    "0xbc78D84Ba0c46dFe32cf2895a19939c86b81a777",  # solvBTC
    "0x152b9d0FdC40C096757F570A51E494bd4b943E50",  # BTC.b
    "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",  # USDC
]


class LFJPriceService(WebPriceService):
    """Custom solvBTC Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom solvBTC Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()
        self.contract_address: Optional[str] = None
        self.contract_abi: Optional[Any] = None
        self.src_len: Optional[int] = None
        self.route: Optional[List[Any]] = None
        self.asset: Optional[str] = None
        self.currency: Optional[str] = None

    def get_LFJ_quote(self, asset: str, currency: str) -> Optional[float]:
        """call the quote function from LFG exchange. Routes are defined based on the pools
        that show up on the LFJ front end for 1(token) vs usdc"""
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=43114)
        if not endpoint:
            logger.error("check avalanche RPC endpoint. unable to get LFJ quotes")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect to endpoint for LFJ source")
            return None
        w3 = ep._web3
        if w3 is None:
            logger.error("Unable to get web3 for avalanche to get LFJ quotes")
            return None
        if asset == "solvbtc":
            self.route = SOLVBTC_ROUTE
        elif asset == "solvbtcbbn":
            self.route = SOLVBTCBBN_ROUTE
        else:
            logger.error("No route list for getting LFJ price (asset not supported)")
            return None
        if currency != "usd":
            logger.error("LFJ source is for usd pairs only!")
            return None
        # get solvbtc/eth ratio
        price_quote = None
        try:
            route = self.route
            amount_in = 1000000000000000000
            contract = w3.eth.contract(address=LFJ_QUOTER_CONTRACT, abi=CONTRACT_ABI)
            contract_function = contract.functions.findBestPathFromAmountIn(route, amount_in)
            data = contract_function.call()
            response_int = data[5][3]
            response_quote = w3.from_wei(response_int, "mwei")
            price_quote = float(response_quote)

        except Exception as e:
            logger.error(f"Error querying LFJ: {e}")

        return price_quote

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """This implementation gets the solvBTC/ETH ratio by checking the oracle
        price from LFJ's price oracle contract
        """
        asset = asset.lower()
        currency = currency.lower()
        lfj_quote = self.get_LFJ_quote(asset=asset, currency=currency)
        logger.info(f"lfj quote for {asset}: {lfj_quote}")
        if lfj_quote is None:
            logger.error(f"lfj_quote is None for {asset} (check source)")
            return None, None

        return lfj_quote, datetime_now_utc()


@dataclass
class LFJPriceSource(PriceSource):
    """Gets data from LFJ contract"""

    asset: str = ""
    currency: str = ""
    service: LFJPriceService = field(default_factory=LFJPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = LFJPriceSource(asset="solvbtcbbn", currency="usd")
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
