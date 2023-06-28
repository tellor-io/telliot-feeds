from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.custom_price import CustomPrice
from telliot_feeds.sources.landx_source import LandXSource

corn = DataFeed(
    query=CustomPrice(identifier="CustomPrice", asset="corn", currency="usd", unit="per_kilogram"),
    source=LandXSource(asset="corn"),
)
wheat = DataFeed(
    query=CustomPrice(identifier="CustomPrice", asset="wheat", currency="usd", unit="per_kilogram"),
    source=LandXSource(asset="wheat"),
)
rice = DataFeed(
    query=CustomPrice(identifier="CustomPrice", asset="rice", currency="usd", unit="per_kilogram"),
    source=LandXSource(asset="rice"),
)
soy = DataFeed(
    query=CustomPrice(identifier="CustomPrice", asset="soy", currency="usd", unit="per_kilogram"),
    source=LandXSource(asset="soy"),
)


if __name__ == "__main__":
    from hexbytes import HexBytes

    print(HexBytes(corn.query.query_id).hex())
    print(HexBytes(wheat.query.query_id).hex())
    print(HexBytes(rice.query.query_id).hex())
    print(HexBytes(soy.query.query_id).hex())
