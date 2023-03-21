from telliot_feeds.queries.query import OracleQuery
from telliot_feeds.queries.query_catalog import query_catalog


def test_query_catalog():
    qlst = query_catalog.find(
        tag="eth-usd-spot", query_id="0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
    )
    assert len(qlst) == 1
    q = qlst[0]
    assert isinstance(q.query, OracleQuery)


def test_find_all():
    """Find all query entries"""
    qlst = query_catalog.find()
    assert len(qlst) > 10


def test_yaml_catalog():
    yml = query_catalog.to_yaml()
    assert isinstance(yml, str)


def test_to_markdown():
    md = query_catalog.to_markdown()
    assert isinstance(md, str)
    print(md)
