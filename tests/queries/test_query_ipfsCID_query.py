""" Unit tests for static queries

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
from telliot_feeds.queries.ipfsCID_query import ipfsCID


def test_ipfsCID_query():
    """Test static query"""
    q = ipfsCID(url="https://raw.githubusercontent.com/tellor-io/dataSpecs/main/README.md")

    assert q.query_data == b'{"type":"ipfsCID","url":"https://raw.githubusercontent.com/tellor-io/dataSpecs/main/README.md"}'

    exp_query_id = "7358f056230629915e1e6a8ef2c2f02496de3de644cbfadfced0449b784f8d47"
    assert q.query_id.hex() == exp_query_id

    exp_query_data = (
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07ipfsCID\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\xa0\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00Dhttps://raw.githubusercontent.com/tellor-io/'
        b'dataSpecs/main/README.md\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
    )

    assert q.query_data == exp_query_data

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "NumericApiResponse"

    url = decode_abi([q.abi[0]["type"]], encoded_param_vals)[0]
    assert (
        url == "https://samples.openweathermap.org/data/2.5/weather?q=Lond`on,uk&appid=b6907d289e10d714a6e88b30761fae22"
    )

    q = NumericApiResponse.get_query_from_data(exp_query_data)
    assert isinstance(q, NumericApiResponse)
    assert q.parseStr == "temp_min, description"


def test_encode_decode():
    q = NumericApiResponse(
        url="https://samples.openweathermap.org/data/2.5/weather?q=Lond`on,uk&appid=b6907d289e10d714a6e88b30761fae22",
        parseStr="temp_min",
    )

    data = 1234.1234
    submit_value = q.value_type.encode(data)
    assert isinstance(submit_value, bytes)

    decoded_data = q.value_type.decode(submit_value)
    assert isinstance(decoded_data, float)
    assert decoded_data == 1234.1234









    submit_value = q.value_type.encode("QmdW4FNKsPS9yykKN5sC7Q53pdWJRz2TXgVRGnZHawP7qe")
    assert isinstance(submit_value, bytes)