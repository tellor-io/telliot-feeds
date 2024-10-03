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

# 2. Set the contract address and ABI
contract_address = "0xee717411f6E44F9feE011835C8E6FAaC5dEfF166"
contract_abi = [
    {
        "inputs": [
            {
                "internalType": "uint8",
                "name": "src_len",
                "type": "uint8"
            },
            {
                "internalType": "contract IERC20Metadata[]",
                "name": "connectors",
                "type": "address[]"
            }
        ],
        "name": "getManyRatesWithConnectors",
        "outputs": [
            {
                "internalType": "uint256[]",
                "name": "rates",
                "type": "uint256[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Function to query the contract
class aerodromeSpotPriceService(WebPriceService):
    """Custom sFRAX Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Custom sFRAX Price Service"
        kwargs["url"] = ""
        super().__init__(**kwargs)
        self.cfg = TelliotConfig()

    def query_contract(src_len, connectors):
        # get endpoint
        endpoint = self.cfg.endpoints.find(chain_id=8453)
        if not endpoint:
            logger.error("Endpoint not found for mainnet to get sfrax_eth_ratio")
            return None
        ep = endpoint[0]
        if not ep.connect():
            logger.error("Unable to connect endpoint for mainnet to get sfrax_eth_ratio")
            return None
        w3 = ep.web3
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        try:
            # Get the contract function
            contract_function = contract.functions.getManyRatesWithConnectors(src_len, connectors)
            # Call the function and return the result
            return contract_function.call()
        except Exception as e:
            print(f"Error querying contract: {e}")
            return None

@dataclass
class aerodromeSpotPriceSource(PriceSource):
    asset: asset = ""
    currency: currency = ""
    service: aerodromeSpotPriceService = field(default_factory=aerodromeSpotPriceService, init=False)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        source = aerodromeSpotPriceSource(src_len=1, connectors=[0xDBFeFD2e8460a6Ee4955A68582F85708BAEA60A3, 0x4200000000000000000000000000000000000006, 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913])
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
