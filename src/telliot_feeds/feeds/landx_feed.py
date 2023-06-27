from telliot_feeds.queries.custom_price import CustomPrice
from telliot_feeds.sources.landx_source import LandXSource
from telliot_feeds.datafeed import DataFeed

corn = DataFeed(
    query=CustomPrice(identifier="CustomPrice", asset="corn", currency="usd", unit="kilograms"),
    source=LandXSource(asset="corn")
)
wheat = DataFeed(
    query=CustomPrice(identifier="CustomPrice", asset="wheat", currency="usd", unit="kilograms"),
    source=LandXSource(asset="wheat")
)
rice = DataFeed(
    query=CustomPrice(identifier="CustomPrice", asset="rice", currency="usd", unit="kilograms"),
    source=LandXSource(asset="rice")
)
soy = DataFeed(
    query=CustomPrice(identifier="CustomPrice", asset="soy", currency="usd", unit="kilograms"),
    source=LandXSource(asset="soy")
)


if __name__ == "__main__":
    from hexbytes import HexBytes
    print(HexBytes(corn.query.query_id).hex())
    print(HexBytes(wheat.query.query_id).hex())
    print(HexBytes(rice.query.query_id).hex())
    print(HexBytes(soy.query.query_id).hex())
