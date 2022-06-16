from telliot_core.data.query_catalog import query_catalog
from telliot_core.queries.query import OracleQuery


def test_query_catalog():
    qlst = query_catalog.find(tag="eth-usd-legacy")
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
