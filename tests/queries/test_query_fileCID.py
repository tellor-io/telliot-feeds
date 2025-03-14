from eth_abi import decode

from telliot_feeds.queries.fileCID import FileCIDQuery


def test_FileCID_query():
    """Test static query"""
    q = FileCIDQuery(
        url="https://raw.githubusercontent.com/tellor-io/dataSpecs/main/README.md",
    )

    exp_query_id = "aa303bc688d50a696455cb5cf10d95e636ed867fb7c928f9187e750f55ee442f"
    assert q.query_id.hex() == exp_query_id
    exp_query_data = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0cFileCIDQuery\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\xa0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00Dhttps://raw.githubusercontent.com/tellor-io/dataSpecs/main/README.md"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )

    assert q.query_data == exp_query_data

    query_type, encoded_param_vals = decode(["string", "bytes"], q.query_data)
    assert query_type == "FileCIDQuery"

    url = decode([q.abi[0]["type"]], encoded_param_vals)[0]
    assert url == "https://raw.githubusercontent.com/tellor-io/dataSpecs/main/README.md"

    q = FileCIDQuery.get_query_from_data(exp_query_data)
    assert isinstance(q, FileCIDQuery)


def test_encode_decode():
    q = FileCIDQuery(
        url="https://raw.githubusercontent.com/tellor-io/dataSpecs/main/README.md",
    )

    data = "QmdW4FNKsPS9yykKN5sC7Q53pdWJRz2TXgVRGnZHawP7qe"
    submit_value = q.value_type.encode(data)
    assert isinstance(submit_value, bytes)

    decoded_data = q.value_type.decode(submit_value)[0]
    assert isinstance(decoded_data, str)
    assert decoded_data == "QmdW4FNKsPS9yykKN5sC7Q53pdWJRz2TXgVRGnZHawP7qe"

    submit_value = q.value_type.encode("QmdW4FNKsPS9yykKN5sC7Q53pdWJRz2TXgVRGnZHawP7qe")
    assert isinstance(submit_value, bytes)
