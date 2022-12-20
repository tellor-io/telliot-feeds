from typing import Any
from typing import Dict

from telliot_feeds.datafeed import DataFeed
from telliot_feeds.feeds.albt_usd_feed import albt_usd_median_feed
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
from telliot_feeds.feeds.gas_price_oracle_feed import gas_price_oracle_feed_example
from telliot_feeds.feeds.idle_usd_feed import idle_usd_median_feed
from telliot_feeds.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feeds.feeds.mkr_usd_feed import mkr_usd_median_feed
from telliot_feeds.feeds.numeric_api_response_feed import numeric_api_response_feed
from telliot_feeds.feeds.numeric_api_response_manual_feed import numeric_api_response_manual_feed
from telliot_feeds.feeds.olympus import ohm_eth_median_feed
from telliot_feeds.feeds.pls_usd_feed import pls_usd_feed
from telliot_feeds.feeds.rai_usd_feed import rai_usd_median_feed
from telliot_feeds.feeds.ric_usd_feed import ric_usd_median_feed
from telliot_feeds.feeds.snapshot_feed import snapshot_feed_example
from telliot_feeds.feeds.snapshot_feed import snapshot_manual_feed
from telliot_feeds.feeds.spot_price_manual_feed import spot_price_manual_feed
from telliot_feeds.feeds.string_query_feed import string_query_feed
from telliot_feeds.feeds.sushi_usd_feed import sushi_usd_median_feed
from telliot_feeds.feeds.tellor_rng_feed import tellor_rng_feed
from telliot_feeds.feeds.tellor_rng_manual_feed import tellor_rng_manual_feed
from telliot_feeds.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feeds.feeds.twap_manual_feed import twap_30d_example_manual_feed
from telliot_feeds.feeds.twap_manual_feed import twap_manual_feed
from telliot_feeds.feeds.usdc_usd_feed import usdc_usd_median_feed
from telliot_feeds.feeds.uspce_feed import uspce_feed
from telliot_feeds.feeds.vesq import vsq_usd_median_feed


CATALOG_FEEDS = {
    "ampleforth-custom": ampl_usd_vwap_feed,
    "ampleforth-uspce": uspce_feed,
    "eth-jpy-spot": eth_jpy_median_feed,
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
    "gas-price-oracle-example": gas_price_oracle_feed_example,
    "eth-usd-30day_volatility": eth_usd_30day_volatility,
    "eur-usd-spot": eur_usd_median_feed,
    "snapshot-proposal-example": snapshot_feed_example,
    "numeric-api-response-example": numeric_api_response_feed,
    "diva-protocol-example": diva_manual_feed,
    "string-query-example": string_query_feed,
    "tellor-rng-example": tellor_rng_feed,
    "twap-eth-usd-example": twap_30d_example_manual_feed,
    "pls-usd-spot": pls_usd_feed,
    "eth-usd-spot": eth_usd_median_feed,
    "btc-usd-spot": btc_usd_median_feed,
    "trb-usd-spot": trb_usd_median_feed,
    "albt-usd-spot": albt_usd_median_feed,
    "rai-usd-spot": rai_usd_median_feed,
}

DATAFEED_BUILDER_MAPPING: Dict[str, DataFeed[Any]] = {
    "SpotPrice": spot_price_manual_feed,
    "DivaProtocol": diva_manual_feed,
    "SnapshotOracle": snapshot_manual_feed,
    "GasPriceOracle": gas_price_oracle_feed,
    "StringQuery": string_query_feed,
    "NumericApiManualResponse": numeric_api_response_manual_feed,
    "NumericApiResponse": numeric_api_response_feed,  # this build will parse and submit response value automatically
    "TWAP": twap_manual_feed,
    "DailyVolatility": daily_volatility_manual_feed,
    "TellorRNG": tellor_rng_feed,
    "TellorRNGManualResponse": tellor_rng_manual_feed,
    "AmpleforthCustomSpotPrice": ampl_usd_vwap_feed,
    "AmpleforthUSPCE": uspce_feed,
}
