from telliot_feeds.queries.json_query import JsonQuery
from telliot_feeds.queries.price.spot_price import SpotPrice


def test_data_interface():
    query_data = b'{"type":"SpotPrice","asset":"btc","currency":"usd"}'
    q = JsonQuery.get_query_from_data(query_data)
    assert isinstance(q, SpotPrice)
    assert q.asset == "btc"
