from dataclasses import dataclass

from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.queries.query import query_from_state


def test_main():
    @dataclass
    class MyQuery(OracleQuery):
        text: str
        val: int = 3

    q = MyQuery("asdf")
    state = q.get_state()
    print(state)
    assert state == {"type": "MyQuery", "text": "asdf", "val": 3}


def test_query_from_state():
    d = {"type": "SpotPrice", "asset": "ohm", "currency": "eth"}
    q = query_from_state(d)
    print(q)
    assert isinstance(q, SpotPrice)
    assert q.asset == "ohm"
