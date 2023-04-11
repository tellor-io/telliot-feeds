from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.mimicry.macro_market_mash_up import MimicryMacroMarketMashup
from telliot_feeds.sources.mimicry.mashup_source import NFTMashupSource


METRIC = "market-cap"
CURRENCY = "usd"
COLLECTIONS = [
    ("ethereum-mainnet", "0x50f5474724e0ee42d9a4e711ccfb275809fd6d4a"),
    ("ethereum-mainnet", "0xf87e31492faf9a91b02ee0deaad50d51d56d5d4d"),
    ("ethereum-mainnet", "0x34d85c9cdeb23fa97cb08333b511ac86e1c4e258"),
]
TOKENS = [
    ("ethereum-mainnet", "sand", "0x3845badade8e6dff049820680d1f14bd3903a5d0"),
    ("ethereum-mainnet", "mana", "0x0f5d2fb29fb7d3cfee444a200298f468908cc942"),
    ("ethereum-mainnet", "ape", "0x4d224452801aced8b2f0aebe155379bb5d594381"),
]

mimicry_mashup_example_feed = DataFeed(
    query=MimicryMacroMarketMashup(metric=METRIC, currency=CURRENCY, collections=COLLECTIONS, tokens=TOKENS),
    source=NFTMashupSource(metric=METRIC, currency=CURRENCY, collections=COLLECTIONS, tokens=TOKENS),
)


metric = None
currency = None
collections = None
tokens = None

mimicry_mashup_feed = DataFeed(
    query=MimicryMacroMarketMashup(metric=metric, currency=currency, collections=collections, tokens=tokens),
    source=NFTMashupSource(metric=metric, currency=currency, collections=collections, tokens=tokens),
)
