from typing import Any
from typing import Dict

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds.ampl_usd_vwap_feed import ampl_usd_vwap_feed
from telliot_feeds.feeds.bct_usd_feed import bct_usd_median_feed
from telliot_feeds.feeds.btc_usd_feed import btc_usd_median_feed
from telliot_feeds.feeds.dai_usd_feed import dai_usd_median_feed
from telliot_feeds.feeds.daily_volatility_manual_feed import daily_volatility_manual_feed
from telliot_feeds.feeds.diva_manual_feed import diva_manual_feed
from telliot_feeds.feeds.eth_jpy_feed import eth_jpy_median_feed
from telliot_feeds.feeds.eth_usd_30day_volatility import eth_usd_30day_volatility
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.feeds.eur_usd_feed import eur_usd_median_feed
from telliot_feeds.feeds.gas_price_oracle_feed import gas_price_oracle_feed
from telliot_feeds.feeds.idle_usd_feed import idle_usd_median_feed
from telliot_feeds.feeds.legacy_request_manual_feed import legacy_request_manual_feed
from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.feeds.mkr_usd_feed import mkr_usd_median_feed
from telliot_feeds.feeds.morphware import morphware_v1_feed
from telliot_feeds.feeds.numeric_api_response_feed import numeric_api_response_feed
from telliot_feeds.feeds.numeric_api_response_manual_feed import numeric_api_response_manual_feed
from telliot_feeds.feeds.olympus import ohm_eth_median_feed
from telliot_feeds.feeds.ric_usd_feed import ric_usd_median_feed
from telliot_feeds.feeds.snapshot_feed import snapshot_manual_feed
from telliot_feeds.feeds.spot_price_manual_feed import spot_price_manual_feed
from telliot_feeds.feeds.string_query_feed import string_query_feed
from telliot_feeds.feeds.sushi_usd_feed import sushi_usd_median_feed
from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.feeds.twap_manual_feed import twap_manual_feed
from telliot_feeds.feeds.usdc_usd_feed import usdc_usd_median_feed
from telliot_feeds.feeds.uspce_feed import uspce_feed
from telliot_feeds.feeds.vesq import vsq_usd_median_feed

# Supported legacy feeds
LEGACY_DATAFEEDS = {
    "1": eth_usd_median_feed,
    "2": btc_usd_median_feed,
    "10": ampl_usd_vwap_feed,
    "41": uspce_feed,
    "50": trb_usd_median_feed,
    "59": eth_jpy_median_feed,
}

CATALOG_FEEDS = {
    "eth-usd-legacy": eth_usd_median_feed,
    "btc-usd-legacy": btc_usd_median_feed,
    "ampl-legacy": ampl_usd_vwap_feed,
    "uspce-legacy": uspce_feed,
    "trb-usd-legacy": trb_usd_median_feed,
    "eth-jpy-legacy": eth_jpy_median_feed,
    "ohm-eth-spot": ohm_eth_median_feed,
    "vsq-usd-spot": vsq_usd_median_feed,
    "bct-usd-spot": bct_usd_median_feed,
    "dai-usd-spot": dai_usd_median_feed,
    "ric-usd-spot": ric_usd_median_feed,
    "idle-usd-spot": idle_usd_median_feed,
    "mkr-usd-spot": mkr_usd_median_feed,
    "sushi-usd-spot": sushi_usd_median_feed,
    "matic-usd-spot": matic_usd_median_feed,
    "usdc-usd-spot": usdc_usd_median_feed,
    "morphware-v1": morphware_v1_feed,
    "gas-price-oracle-example": gas_price_oracle_feed,
    "eth-usd-30day_volatility": eth_usd_30day_volatility,
    "eur-usd-spot": eur_usd_median_feed,
    "snapshot-proposal-example": snapshot_manual_feed,
}

DATAFEED_BUILDER_MAPPING: Dict[str, DataFeed[Any]] = {
    "SpotPrice": spot_price_manual_feed,
    # "apiquery",
    "DivaProtocol": diva_manual_feed,
    "SnapshotOracle": snapshot_manual_feed,
    "GasPriceOracle": gas_price_oracle_feed,
    "NumericApiResponse": numeric_api_response_feed,
    "StringQueryOracle": string_query_feed,
    "NumericApiManualResponse": numeric_api_response_manual_feed,
    "NumericApiResponse": numeric_api_response_feed,  # this build will parse and submit response value automatically
    "LegacyRequest": legacy_request_manual_feed,
    "TWAP": twap_manual_feed,
    "DailyVolatility": daily_volatility_manual_feed,
    # "morphware",
}
