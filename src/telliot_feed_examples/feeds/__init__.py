from telliot_feed_examples.feeds.ampl_usd_vwap_feed import ampl_usd_vwap_feed
from telliot_feed_examples.feeds.bct_usd_feed import bct_usd_median_feed
from telliot_feed_examples.feeds.btc_usd_feed import btc_usd_median_feed
from telliot_feed_examples.feeds.dai_usd_feed import dai_usd_median_feed
from telliot_feed_examples.feeds.eth_jpy_feed import eth_jpy_median_feed
from telliot_feed_examples.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feed_examples.feeds.idle_usd_feed import idle_usd_median_feed
from telliot_feed_examples.feeds.matic_usd_feed import matic_usd_median_feed
from telliot_feed_examples.feeds.mkr_usd_feed import mkr_usd_median_feed
from telliot_feed_examples.feeds.olympus import ohm_eth_median_feed
from telliot_feed_examples.feeds.ric_usd_feed import ric_usd_median_feed
from telliot_feed_examples.feeds.sushi_usd_feed import sushi_usd_median_feed
from telliot_feed_examples.feeds.trb_usd_feed import trb_usd_median_feed
from telliot_feed_examples.feeds.usdc_usd_feed import usdc_usd_median_feed
from telliot_feed_examples.feeds.uspce_feed import uspce_feed
from telliot_feed_examples.feeds.vesq import vsq_usd_median_feed


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
}
