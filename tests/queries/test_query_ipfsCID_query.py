from eth_abi import decode_abi


from telliot_feeds.queries.ipfsCID_query import ipfsCID


def test_ipfsCID_query():
    """Test static query"""
    q = ipfsCID(
        url="https://raw.githubusercontent.com/tellor-io/dataSpecs/main/README.md",
    )

    exp_query_id = "da3b2bd336f0d02af24c096b613920170cabc486a3537596fa5a34d26e2927d1"
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
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    )

    assert q.query_data == exp_query_data

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "ipfsCID"

    url = decode_abi([q.abi[0]["type"]], encoded_param_vals)[0]
    assert (
        url == "https://raw.githubusercontent.com/tellor-io/dataSpecs/main/README.md"
    )

    q = ipfsCID.get_query_from_data(exp_query_data)
    assert isinstance(q, ipfsCID)


def test_encode_decode():
    q = ipfsCID(
        url="https://raw.githubusercontent.com/tellor-io/dataSpecs/main/README.md",
    )

    data = "QmdW4FNKsPS9yykKN5sC7Q53pdWJRz2TXgVRGnZHawP7qe"
    submit_value = q.value_type.encode(data)
    assert isinstance(submit_value, bytes)

    decoded_data = q.value_type.decode(submit_value)
    assert isinstance(decoded_data, str)
    assert decoded_data == "QmdW4FNKsPS9yykKN5sC7Q53pdWJRz2TXgVRGnZHawP7qe"









    submit_value = q.value_type.encode("QmdW4FNKsPS9yykKN5sC7Q53pdWJRz2TXgVRGnZHawP7qe")
    assert isinstance(submit_value, bytes)