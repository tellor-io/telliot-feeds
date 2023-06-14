SUPPORTED_HISTORICAL_PRICE_PAIRS = {
    "BTC/USD",
    "ETH/USD",
}
SUPPORTED_COLLATERAL_TOKEN_SYMBOLS = {"dUSD"}
DIVA_DIAMOND_ADDRESS = "0x2C9c47E7d254e493f02acfB410864b9a86c28e1D"
DIVA_TELLOR_MIDDLEWARE_ADDRESS = "0x7950DB13cc37774614B0AA406e42a4C4f0BF26a6"
# playgroud adapter (10 sec dispute period)
# DIVA_TELLOR_MIDDLEWARE_ADDRESS = "0x0625855A4D292216ADEFA8043cDc69a6c99724C9"
# for fetching pool data. network name is appended to this (e.g. "mumbai")
BASE_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/divaprotocol/diva-protocol-v1-"
