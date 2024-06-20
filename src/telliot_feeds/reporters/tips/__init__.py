import logging
from typing import Optional

from multicall.constants import MULTICALL2_ADDRESSES
from multicall.constants import MULTICALL3_ADDRESSES
from multicall.constants import Network
from multicall.constants import NO_STATE_OVERRIDE

from telliot_feeds.queries.query_catalog import query_catalog

logger = logging.getLogger(__name__)


# add testnet support for multicall that aren't avaialable in the package
def add_multicall_support(
    network: str,
    network_id: int,
    state_override: bool = True,
    multicall2_address: Optional[str] = None,
    multicall3_address: Optional[str] = None,
) -> None:
    """Add support for a network that doesn't have multicall support in the package"""
    if not hasattr(Network, network):
        setattr(Network, network, network_id)
        attr = getattr(Network, network)
        if not state_override:
            # Gnosis chain doesn't have state override so we need to add it
            # to the list of chains that don't have state override in the package
            # to avoid errors
            NO_STATE_OVERRIDE.append(attr)
        if multicall2_address:
            MULTICALL2_ADDRESSES[attr] = multicall2_address
        else:
            MULTICALL3_ADDRESSES[attr] = multicall3_address
    else:
        logger.info(f"Network {network} already exists in multicall package")


add_multicall_support(
    network="Chiado",
    network_id=10200,
    state_override=False,
    multicall3_address="0x08e08170712c7751b45b38865B97A50855c8ab13",
)

add_multicall_support(
    network="Filecoin Hyperspace Testnet",
    network_id=3141,
    state_override=False,
    multicall3_address="0x08e08170712c7751b45b38865B97A50855c8ab13",
)

add_multicall_support(
    network="Filecoin calibration Testnet",
    network_id=314159,
    state_override=False,
    multicall3_address="0xd0af7dcea1434e4fb77ac9769d4bac5fe713fd7f",
)

add_multicall_support(
    network="Filecoin",
    network_id=314,
    state_override=False,
    multicall3_address="0x08ba1ac7f15f2215f27b5403a89bed22ceb70cfb",
)

add_multicall_support(
    network="Pulsechain",
    network_id=369,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Pulsechain Testnet",
    network_id=943,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Manta Testnet",
    network_id=3441005,
    state_override=False,
    multicall3_address="0x211B1643b95Fe76f11eD8880EE810ABD9A4cf56C",
)

add_multicall_support(
    network="Base Goerli",
    network_id=84531,
    state_override=False,
    multicall3_address="0x8252eA5560755e6707c97C72e008CF22Ce0ca85F",
)

add_multicall_support(
    network="Mantle Testnet",
    network_id=5001,
    state_override=False,
    multicall3_address="0xbc3295180704476e4D40400b39d1d75892D91327",
)

add_multicall_support(
    network="Mantle",
    network_id=5000,
    state_override=False,
    multicall3_address="0x5Dbd743481a4027d6632E169592860a1Ca38C637",
)

add_multicall_support(
    network="Polygon zkEVM Cardona Testnet",
    network_id=2442,
    state_override=False,
    multicall3_address="0x7Fa83caCD47589fB192A680CD809430D995f98e8",
)

add_multicall_support(
    network="Polygon zkEVM",
    network_id=1101,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Linea Goerli",
    network_id=59140,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Linea",
    network_id=59144,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Linea Sepolia",
    network_id=59141,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Kyoto Testnet",
    network_id=1998,
    state_override=False,
    multicall3_address="0x0D474E0905F99ED1E06F727938B6cF851340c865",
)

add_multicall_support(
    network="Skale Europa Testnet",
    network_id=1444673419,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Skale Europa Mainnet",
    network_id=2046399126,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="zkSync Era Mainnet",
    network_id=324,
    state_override=False,
    multicall3_address="0xF9cda624FBC7e059355ce98a31693d299FACd963",
)

add_multicall_support(
    network="zkSync Era Sepolia Testnet",
    network_id=300,
    state_override=False,
    multicall3_address="0xF9cda624FBC7e059355ce98a31693d299FACd963",
)

add_multicall_support(
    network="Polygon Amoy Testnet",
    network_id=80002,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Optimism Sepolia Testnet",
    network_id=11155420,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Arbitrum Sepolia Testnet",
    network_id=421614,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Mantle Sepolia Testnet",
    network_id=5003,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Base Sepolia Testnet",
    network_id=84532,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Fraxtal Testnet",
    network_id=2522,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="Fraxtal Mainnet",
    network_id=252,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="puff-bob-jznbxtoq7h",
    network_id=111,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="bob",
    network_id=60808,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="mode-sepolia-vtnhnpim72",
    network_id=919,
    state_override=False,
    multicall3_address="0xcA11bde05977b3631167028862bE2a173976CA11",
)

add_multicall_support(
    network="telos EVM testnet",
    network_id=41,
    state_override=False,
    multicall3_address="0x2aD2e05661Ff30BCF1D58c311eAD5D5f4ECEeFDf",
)

add_multicall_support(
    network="Atleta Olympia",
    network_id=2340,
    state_override=False,
    multicall3_address="0x2aD2e05661Ff30BCF1D58c311eAD5D5f4ECEeFDf",
)

add_multicall_support(
    network="Taraxa Testnet",
    network_id=842,
    state_override=False,
    multicall3_address="0x33e45BbfDa4687Aab280c2c93fa027ba61c4A0eA",
)

add_multicall_support(
    network="Rari Chain Testnet",
    network_id=1918988905,
    state_override=False,
    multicall3_address="0xFEf60Df67Ac10Ebee1cd70Ef9e7AF6AF6c449bf4",
)

CATALOG_QUERY_IDS = {query_catalog._entries[tag].query.query_id: tag for tag in query_catalog._entries}
CATALOG_QUERY_DATA = {query_catalog._entries[tag].query.query_data: tag for tag in query_catalog._entries}
# A list of query types that have a generic source that can take any properly formatted inputs and return a price
# unlike manual input sources that prompt user input. This allows tip listener to fetch prices when needing to check
# threshold conditions
TYPES_WITH_GENERIC_SOURCE = ["MimicryMacroMarketMashup", "MimicryCollectionStat"]
