from multicall.constants import MULTICALL2_ADDRESSES
from multicall.constants import MULTICALL3_ADDRESSES
from multicall.constants import Network

from telliot_feeds.queries.query_catalog import query_catalog


# add testnet support for multicall that aren't avaialable in the package
Network.PulsechainTestnet = 941
MULTICALL2_ADDRESSES[Network.PulsechainTestnet] = "0x959a437F1444DaDaC8aF997E71EAF0479c810267"
Network.Chiado = 10200
MULTICALL3_ADDRESSES[Network.Chiado] = "0x08e08170712c7751b45b38865B97A50855c8ab13"


CATALOG_QUERY_IDS = {query_catalog._entries[tag].query.query_id: tag for tag in query_catalog._entries}
CATALOG_QUERY_DATA = {query_catalog._entries[tag].query.query_data: tag for tag in query_catalog._entries}
