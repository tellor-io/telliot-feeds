"""example feed"""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.mimicry.mimicry_macro_market_mash_up import MimicryMacroMarketMashup
from telliot_feeds.sources.mimicry.mimicry_mashup_source import NFTMashupSource


metric = "market-cap"
currency = "usd"
collections = (
    ("ethereum-mainnet", "0x50f5474724e0ee42d9a4e711ccfb275809fd6d4a"),
    ("ethereum-mainnet", "0xf87e31492faf9a91b02ee0deaad50d51d56d5d4d"),
    ("ethereum-mainnet", "0x34d85c9cdeb23fa97cb08333b511ac86e1c4e258"),
)
tokens = (
    ("ethereum-mainnet", "sand", "0x3845badAde8e6dFF049820680d1F14bD3903a5d0"),
    ("ethereum-mainnet", "mana", "0x0F5D2fB29fb7d3CFeE444a200298f468908cC942"),
    ("ethereum-mainnet", "ape", "0x4d224452801ACEd8B2F0aebE155379bb5D594381"),
)

mimicry_mashup_feed_example = DataFeed(
    query=MimicryMacroMarketMashup(metric=metric, currency=currency, collections=collections, tokens=tokens),
    source=NFTMashupSource(metric=metric, currency=currency, collections=collections, tokens=tokens),
)
