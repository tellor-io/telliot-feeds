from hexbytes import HexBytes

from telliot_feeds.feeds.mimicry.macro_market_mashup_feed import COLLECTIONS
from telliot_feeds.feeds.mimicry.macro_market_mashup_feed import TOKENS
from telliot_feeds.integrations.diva_protocol import DIVA_DIAMOND_ADDRESS
from telliot_feeds.queries.ampleforth.ampl_usd_vwap import AmpleforthCustomSpotPrice
from telliot_feeds.queries.ampleforth.uspce import AmpleforthUSPCE
from telliot_feeds.queries.btc_balance import BTCBalance
from telliot_feeds.queries.btc_balance_current import BTCBalanceCurrent
from telliot_feeds.queries.catalog import Catalog
from telliot_feeds.queries.custom_price import CustomPrice
from telliot_feeds.queries.daily_volatility import DailyVolatility
from telliot_feeds.queries.diva_protocol import DIVAProtocol
from telliot_feeds.queries.evm_balance import EVMBalance
from telliot_feeds.queries.evm_balance_current import EVMBalanceCurrent
from telliot_feeds.queries.evm_call import EVMCall
from telliot_feeds.queries.fileCID import FileCIDQuery
from telliot_feeds.queries.gas_price_oracle import GasPriceOracle
from telliot_feeds.queries.mimicry.collection_stat import MimicryCollectionStat
from telliot_feeds.queries.mimicry.macro_market_mash_up import MimicryMacroMarketMashup
from telliot_feeds.queries.mimicry.nft_market_index import MimicryNFTMarketIndex
from telliot_feeds.queries.numeric_api_response_query import NumericApiResponse
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.queries.price.twap import TWAP
from telliot_feeds.queries.snapshot import Snapshot
from telliot_feeds.queries.string_query import StringQuery
from telliot_feeds.queries.tellor_rng import TellorRNG

"""Main instance of the Query Catalog."""
query_catalog = Catalog()

# --------------------------------------------------------------------------------------
# Query Catalog Entries
# --------------------------------------------------------------------------------------

query_catalog.add_entry(tag="trb-usd-spot", title="TRB/USD spot price", q=SpotPrice(asset="trb", currency="usd"))

query_catalog.add_entry(
    tag="ohm-eth-spot",
    title="OHM/ETH spot price",
    q=SpotPrice(asset="ohm", currency="eth"),
    active=True,
)

query_catalog.add_entry(
    tag="vsq-usd-spot",
    title="VSQ/USD spot price",
    q=SpotPrice(asset="vsq", currency="usd"),
)

query_catalog.add_entry(
    tag="bct-usd-spot",
    title="BCT/USD spot price",
    q=SpotPrice(asset="bct", currency="usd"),
)

query_catalog.add_entry(
    tag="dai-usd-spot",
    title="DAI/USD spot price",
    q=SpotPrice(asset="dai", currency="usd"),
)

query_catalog.add_entry(
    tag="ric-usd-spot",
    title="RIC/USD spot price",
    q=SpotPrice(asset="ric", currency="usd"),
)

query_catalog.add_entry(
    tag="idle-usd-spot",
    title="IDLE/USD spot price",
    q=SpotPrice(asset="idle", currency="usd"),
)

query_catalog.add_entry(
    tag="mkr-usd-spot",
    title="MKR/USD spot price",
    q=SpotPrice(asset="mkr", currency="usd"),
)

query_catalog.add_entry(
    tag="sushi-usd-spot",
    title="SUSHI/USD spot price",
    q=SpotPrice(asset="sushi", currency="usd"),
)

query_catalog.add_entry(
    tag="matic-usd-spot",
    title="MATIC/USD spot price",
    q=SpotPrice(asset="matic", currency="usd"),
)

query_catalog.add_entry(
    tag="usdc-usd-spot",
    title="USDC/USD spot price",
    q=SpotPrice(asset="usdc", currency="usd"),
)


query_catalog.add_entry(
    tag="gas-price-oracle-example",
    title="Gas Price Oracle Mainnet 7/1/2022",
    q=GasPriceOracle(1, 1656633600),
)

query_catalog.add_entry(tag="eur-usd-spot", title="EUR/USD spot price", q=SpotPrice(asset="eur", currency="usd"))
# Source:
# https://snapshot.org/#/aave.eth/proposal/0xcce9760adea906176940ae5fd05bc007cc9252b524832065800635484cb5cb57
query_catalog.add_entry(
    tag="snapshot-proposal-example",
    title="Snapshot proposal example",
    q=Snapshot(proposalId="cce9760adea906176940ae5fd05bc007cc9252b524832065800635484cb5cb57"),
)

query_catalog.add_entry(
    tag="eth-usd-30day_volatility",
    title="30-Day ETH/USD volatility",
    q=DailyVolatility(asset="eth", currency="usd", days=30),
)
query_catalog.add_entry(
    tag="numeric-api-response-example",
    title="Numeric API response example",
    q=NumericApiResponse(
        url="https://api.coingecko.com/api/v3/simple/price?ids=garlicoin&vs_currencies=usd", parseStr="garlicoin, usd"
    ),
)
query_catalog.add_entry(
    tag="diva-protocol-example",
    title="DIVA Protocol example",
    q=DIVAProtocol(
        poolId=HexBytes("0x29a5e6c77d5ba659b3c6688799a02beb98b061c1ba6431c1e660cd8454cdc984"),
        divaDiamond=DIVA_DIAMOND_ADDRESS,
        chainId=80001,
    ),
)
query_catalog.add_entry(
    tag="string-query-example", title="String query example", q=StringQuery(text="Where is the Atlantic ocean?")
)

query_catalog.add_entry(
    tag="pls-usd-spot",
    title="PLS/USD spot price",
    q=SpotPrice(asset="pls", currency="usd"),
)

query_catalog.add_entry(
    tag="eth-usd-spot",
    title="ETH/USD spot price",
    q=SpotPrice(asset="eth", currency="usd"),
)

query_catalog.add_entry(
    tag="btc-usd-spot",
    title="BTC/USD spot price",
    q=SpotPrice(asset="btc", currency="usd"),
)

query_catalog.add_entry(tag="tellor-rng-example", title="Tellor RNG", q=TellorRNG(timestamp=1660567612))
query_catalog.add_entry(
    tag="twap-eth-usd-example", title="Time Weighted Average Price", q=TWAP(asset="eth", currency="usd", timespan=86400)
)

query_catalog.add_entry(
    tag="ampleforth-uspce",
    title="USPCE",
    q=AmpleforthUSPCE(),
)
query_catalog.add_entry(
    tag="ampleforth-custom",
    title="AMPL/USD VWAP",
    q=AmpleforthCustomSpotPrice(),
)
query_catalog.add_entry(
    tag="albt-usd-spot",
    title="ALBT/USD spot price",
    q=SpotPrice(asset="albt", currency="usd"),
)

query_catalog.add_entry(
    tag="rai-usd-spot",
    title="RAI/USD spot price",
    q=SpotPrice(asset="rai", currency="usd"),
)

query_catalog.add_entry(
    tag="xdai-usd-spot",
    title="XDAI/USD spot price",
    q=SpotPrice(asset="xdai", currency="usd"),
)

query_catalog.add_entry(
    tag="eth-btc-spot",
    title="ETH/BTC spot price",
    q=SpotPrice(asset="eth", currency="btc"),
)

query_catalog.add_entry(
    tag="evm-call-example",
    title="EVM call example",
    q=EVMCall(
        chainId=1,
        contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata=b"\x18\x16\x0d\xdd",
    ),
)

query_catalog.add_entry(
    tag="avax-usd-spot",
    title="AVAX/USD spot price",
    q=SpotPrice(asset="avax", currency="usd"),
)

query_catalog.add_entry(
    tag="aave-usd-spot",
    title="AAVE/USD spot price",
    q=SpotPrice(asset="aave", currency="usd"),
)

query_catalog.add_entry(
    tag="badger-usd-spot",
    title="BADGER/USD spot price",
    q=SpotPrice(asset="badger", currency="usd"),
)

query_catalog.add_entry(
    tag="bch-usd-spot",
    title="BCH/USD spot price",
    q=SpotPrice(asset="bch", currency="usd"),
)

query_catalog.add_entry(
    tag="comp-usd-spot",
    title="COMP/USD spot price",
    q=SpotPrice(asset="comp", currency="usd"),
)

query_catalog.add_entry(
    tag="crv-usd-spot",
    title="CRV/USD spot price",
    q=SpotPrice(asset="crv", currency="usd"),
)

query_catalog.add_entry(
    tag="doge-usd-spot",
    title="DOGE/USD spot price",
    q=SpotPrice(asset="doge", currency="usd"),
)

query_catalog.add_entry(
    tag="dot-usd-spot",
    title="DOT/USD spot price",
    q=SpotPrice(asset="dot", currency="usd"),
)

query_catalog.add_entry(
    tag="eul-usd-spot",
    title="EUL/USD spot price",
    q=SpotPrice(asset="eul", currency="usd"),
)

query_catalog.add_entry(
    tag="fil-usd-spot",
    title="FIL/USD spot price",
    q=SpotPrice(asset="fil", currency="usd"),
)

query_catalog.add_entry(
    tag="gno-usd-spot",
    title="GNO/USD spot price",
    q=SpotPrice(asset="gno", currency="usd"),
)

query_catalog.add_entry(
    tag="link-usd-spot",
    title="LINK/USD spot price",
    q=SpotPrice(asset="link", currency="usd"),
)

query_catalog.add_entry(
    tag="ltc-usd-spot",
    title="LTC/USD spot price",
    q=SpotPrice(asset="ltc", currency="usd"),
)

query_catalog.add_entry(
    tag="shib-usd-spot",
    title="SHIB/USD spot price",
    q=SpotPrice(asset="shib", currency="usd"),
)

query_catalog.add_entry(
    tag="uni-usd-spot",
    title="UNI/USD spot price",
    q=SpotPrice(asset="uni", currency="usd"),
)

query_catalog.add_entry(
    tag="usdt-usd-spot",
    title="USDT/USD spot price",
    q=SpotPrice(asset="usdt", currency="usd"),
)

query_catalog.add_entry(
    tag="yfi-usd-spot",
    title="YFI/USD spot price",
    q=SpotPrice(asset="yfi", currency="usd"),
)

query_catalog.add_entry(
    tag="mimicry-crypto-coven-tami",
    title="Crypto Coven TAMI calculation for Mimicry",
    q=MimicryCollectionStat(collectionAddress="0x5180db8F5c931aaE63c74266b211F580155ecac8", chainId=1, metric=0),
)

query_catalog.add_entry(
    tag="mimicry-nft-index-usd",
    title="NFT Market Index usd",
    q=MimicryNFTMarketIndex(chain="ethereum", currency="usd"),
    active=True,
)

query_catalog.add_entry(
    tag="mimicry-nft-index-eth",
    title="NFT Market Index eth",
    q=MimicryNFTMarketIndex(chain="ethereum", currency="eth"),
    active=True,
)

query_catalog.add_entry(
    tag="mimicry-mashup-example",
    title="NFT market cap mashup",
    q=MimicryMacroMarketMashup(metric="market-cap", currency="usd", collections=COLLECTIONS, tokens=TOKENS),
    active=True,
)

query_catalog.add_entry(
    tag="steth-btc-spot",
    title="STETH/BTC spot price",
    q=SpotPrice(asset="steth", currency="btc"),
)

query_catalog.add_entry(
    tag="steth-usd-spot",
    title="STETH/USD spot price",
    q=SpotPrice(asset="steth", currency="usd"),
)

query_catalog.add_entry(
    tag="reth-btc-spot",
    title="RETH/BTC spot price",
    q=SpotPrice(asset="reth", currency="btc"),
)

query_catalog.add_entry(
    tag="reth-usd-spot",
    title="RETH/USD spot price",
    q=SpotPrice(asset="reth", currency="usd"),
)

query_catalog.add_entry(
    tag="wsteth-usd-spot",
    title="WSTETH/USD spot price",
    q=SpotPrice(asset="wsteth", currency="usd"),
)

query_catalog.add_entry(
    tag="wsteth-eth-spot",
    title="WSTETH/ETH spot price",
    q=SpotPrice(asset="wsteth", currency="eth"),
)

query_catalog.add_entry(
    tag="op-usd-spot",
    title="OP/USD spot price",
    q=SpotPrice(asset="op", currency="usd"),
)

query_catalog.add_entry(
    tag="grt-usd-spot",
    title="GRT/USD spot price",
    q=SpotPrice(asset="grt", currency="usd"),
)

query_catalog.add_entry(
    tag="cny-usd-spot",
    title="CNY/USD spot price",
    q=SpotPrice(asset="cny", currency="usd"),
)

query_catalog.add_entry(
    tag="eth-jpy-spot",
    title="ETH/JPY spot price",
    q=SpotPrice(asset="eth", currency="jpy"),
)

query_catalog.add_entry(
    tag="brl-usd-spot",
    title="BRL/USD spot price",
    q=SpotPrice(asset="brl", currency="usd"),
)

query_catalog.add_entry(
    tag="corn-usd-custom",
    title="Corn price in usd per kilogram",
    q=CustomPrice(identifier="landx", asset="corn", currency="usd", unit="per_kilogram"),
)

query_catalog.add_entry(
    tag="rice-usd-custom",
    title="Rice price in usd per kilogram",
    q=CustomPrice(identifier="landx", asset="rice", currency="usd", unit="per_kilogram"),
)

query_catalog.add_entry(
    tag="wheat-usd-custom",
    title="Wheat price in usd per kilogram",
    q=CustomPrice(identifier="landx", asset="wheat", currency="usd", unit="per_kilogram"),
)

query_catalog.add_entry(
    tag="soy-usd-custom",
    title="Soy price in usd per kilogram",
    q=CustomPrice(identifier="landx", asset="soy", currency="usd", unit="per_kilogram"),
)

query_catalog.add_entry(
    tag="ousd-usd-spot",
    title="OUSD/USD spot price",
    q=SpotPrice(asset="ousd", currency="usd"),
)

query_catalog.add_entry(
    tag="oeth-eth-spot",
    title="OETH/ETH spot price",
    q=SpotPrice(asset="oeth", currency="eth"),
)

query_catalog.add_entry(
    tag="wld-usd-spot",
    title="WLD/USD spot price",
    q=SpotPrice(asset="wld", currency="usd"),
)

query_catalog.add_entry(
    tag="sweth-usd-spot",
    title="SWETH/USD spot price",
    q=SpotPrice(asset="sweth", currency="usd"),
)

query_catalog.add_entry(
    tag="diva-usd-spot",
    title="DIVA/USD spot price",
    q=SpotPrice(asset="diva", currency="usd"),
)

query_catalog.add_entry(
    tag="cbeth-usd-spot",
    title="CBETH/USD spot price",
    q=SpotPrice(asset="cbeth", currency="usd"),
)

query_catalog.add_entry(
    tag="wbeth-usd-spot",
    title="WBETH/USD spot price",
    q=SpotPrice(asset="wbeth", currency="usd"),
)

query_catalog.add_entry(
    tag="oeth-usd-spot",
    title="OETH/USD spot price",
    q=SpotPrice(asset="oeth", currency="usd"),
)

query_catalog.add_entry(
    tag="pyth-usd-spot",
    title="PYTH/USD spot price",
    q=SpotPrice(asset="pyth", currency="usd"),
)

query_catalog.add_entry(
    tag="ogv-eth-spot",
    title="OGV/ETH spot price",
    q=SpotPrice(asset="ogv", currency="eth"),
)

query_catalog.add_entry(
    tag="brc20-ordi-usd-spot",
    title="ORDI/USD spot price",
    q=CustomPrice(identifier="brc20", asset="ordi", currency="usd", unit=""),
)

query_catalog.add_entry(
    tag="meth-usd-spot",
    title="METH/USD spot price",
    q=SpotPrice(asset="meth", currency="usd"),
)

query_catalog.add_entry(
    tag="wbtc-usd-spot",
    title="WBTC/USD spot price",
    q=SpotPrice(asset="wbtc", currency="usd"),
)

query_catalog.add_entry(
    tag="mnt-usd-spot",
    title="MNT/USD spot price",
    q=SpotPrice(asset="mnt", currency="usd"),
)

query_catalog.add_entry(
    tag="usdy-usd-spot",
    title="USDY/USD spot price",
    q=SpotPrice(asset="usdy", currency="usd"),
)

query_catalog.add_entry(
    tag="wmnt-usd-spot",
    title="WMNT/USD spot price",
    q=SpotPrice(asset="wmnt", currency="usd"),
)

query_catalog.add_entry(
    tag="btc-bal-example",
    title="BTC balance example",
    q=BTCBalance(btcAddress="bc1q06ywseed6sc3x2fafppchefqq8v9cqd0l6vx03", timestamp=1706051389),
)

query_catalog.add_entry(
    tag="btc-bal-current-example",
    title="BTC balance current example",
    q=BTCBalanceCurrent(btcAddress="bc1q06ywseed6sc3x2fafppchefqq8v9cqd0l6vx03"),
)

query_catalog.add_entry(
    tag="evm-bal-example",
    title="EVM balance example",
    q=EVMBalance(chainId=11155111, evmAddress="0x210766226c54CDD6bD0401749D43E7a5585e3868", timestamp=1706302197),
)

query_catalog.add_entry(
    tag="evm-bal-current-example",
    title="EVM balance current example",
    q=EVMBalanceCurrent(chainId=11155111, evmAddress="0x210766226c54CDD6bD0401749D43E7a5585e3868"),
)

query_catalog.add_entry(
    tag="primeeth-eth-spot",
    title="PRIMEETH/ETH spot price",
    q=SpotPrice(asset="primeeth", currency="eth"),
)

query_catalog.add_entry(
    tag="usdm-usd-spot",
    title="USDM/USD spot price",
    q=SpotPrice(asset="usdm", currency="usd"),
)

query_catalog.add_entry(
    tag="wusdm-usd-spot",
    title="WUSDM/USD spot price",
    q=SpotPrice(asset="wusdm", currency="usd"),
)

query_catalog.add_entry(
    tag="sdai-usd-spot",
    title="SDAI/USD spot price",
    q=SpotPrice(asset="sdai", currency="usd"),
)

query_catalog.add_entry(
    tag="sfrax-usd-spot",
    title="SFRAX/USD spot price",
    q=SpotPrice(asset="sfrax", currency="usd"),
)

query_catalog.add_entry(
    tag="frax-usd-spot",
    title="FRAX/USD spot price",
    q=SpotPrice(asset="frax", currency="usd"),
)

query_catalog.add_entry(
    tag="gyd-usd-spot",
    title="GYD/USD spot price",
    q=SpotPrice(asset="gyd", currency="usd"),
)

query_catalog.add_entry(
    tag="leth-usd-spot",
    title="LETH/USD spot price",
    q=SpotPrice(asset="leth", currency="usd"),
)

query_catalog.add_entry(
    tag="frxeth-usd-spot",
    title="FRXETH/USD spot price",
    q=SpotPrice(asset="frxeth", currency="usd"),
)

query_catalog.add_entry(
    tag="filecid-query-example",
    title="FileCID query example",
    q=FileCIDQuery(url="https://raw.githubusercontent.com/tellor-io/dataSpecs/main/README.md"),
)

query_catalog.add_entry(
    tag="ezeth-usd-spot",
    title="EZETH/USD spot price",
    q=SpotPrice(asset="ezeth", currency="usd"),
)

query_catalog.add_entry(
    tag="weeth-usd-spot",
    title="WEETH/USD spot price",
    q=SpotPrice(asset="weeth", currency="usd"),
)

query_catalog.add_entry(
    tag="wrseth-usd-spot",
    title="WRSETH/USD spot price",
    q=SpotPrice(asset="wrseth", currency="usd"),
)

query_catalog.add_entry(
    tag="rseth-usd-spot",
    title="RSETH/USD spot price",
    q=SpotPrice(asset="rseth", currency="usd"),
)

query_catalog.add_entry(
    tag="mode-usd-spot",
    title="MODE/USD spot price",
    q=SpotPrice(asset="mode", currency="usd"),
)

query_catalog.add_entry(
    tag="tlos-usd-spot",
    title="TLOS/USD spot price",
    q=SpotPrice(asset="tlos", currency="usd"),
)

query_catalog.add_entry(
    tag="tara-usd-spot",
    title="TARA/USD spot price",
    q=SpotPrice(asset="tara", currency="usd"),
)
