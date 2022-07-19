""" Unit tests for static queries

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from telliot_feeds.queries.string_query import StringQuery


def test_static_query():
    """Test static query"""
    q = StringQuery(text="What is the meaning of life")

    assert q.query_data == b'{"type":"StringQuery","text":"What is the meaning of life"}'

    submit_value = q.value_type.encode("Please refer to: https://en.wikipedia.org/wiki/Meaning_of_life")
    assert isinstance(submit_value, bytes)
