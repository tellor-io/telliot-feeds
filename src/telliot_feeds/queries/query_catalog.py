from telliot_feeds.queries.ampleforth.ampl_usd_vwap import AmpleforthCustomSpotPrice
from telliot_feeds.queries.ampleforth.uspce import AmpleforthUSPCE
from telliot_feeds.queries.catalog import Catalog
from telliot_feeds.queries.daily_volatility import DailyVolatility
from telliot_feeds.queries.diva_protocol import DIVAProtocol
from telliot_feeds.queries.gas_price_oracle import GasPriceOracle
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
    title="Diva protocol example",
    q=DIVAProtocol(poolId=1234, divaDiamond="0xebBAA31B1Ebd727A1a42e71dC15E304aD8905211", chainId=3),
)
query_catalog.add_entry(
    tag="string-query-example", title="String query example", q=StringQuery(text="Where is the Atlantic ocean?")
)

query_catalog.add_entry(
    tag="pls-usd-spot",
    title="Pulsechain LiquidLoans feed",
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
