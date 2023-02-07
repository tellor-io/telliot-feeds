from eth_abi import decode_abi

from telliot_feeds.queries.evm_call import EVMCall

# from eth_abi import encode_abi


def test_evm_call_constructor():
    """Validate EVMCall query."""
    # Chain ID, address, and calldata for retrieving total supply of TRB on Ethereum mainnet
    q = EVMCall(
        chainId=1,
        contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata=b"\x18\x16\x0d\xdd",
    )
    # expected query data generated with:
    # https://abi.hashex.org/
    expected_query_data = (
        "000000000000000000000000000000000000000000000000000000000000004"
        "0000000000000000000000000000000000000000000000000000000000000008"
        "0000000000000000000000000000000000000000000000000000000000000000"
        "745564d43616c6c0000000000000000000000000000000000000000000000000"
        "000000000000000000000000000000000000000000000000000000000000000a"
        "00000000000000000000000000000000000000000000000000000000000000001"
        "00000000000000000000000088df592f8eb5d7bd38bfef7deb0fbc02cf3778a00"
        "00000000000000000000000000000000000000000000000000000000000006000"
        "0000000000000000000000000000000000000000000000000000000000000418160ddd"
        "00000000000000000000000000000000000000000000000000000000"
    )
    print(q.query_data.hex())
    print(q.query_id.hex())

    assert q.query_data.hex() == expected_query_data

    query_type, _ = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "EVMCall"

    exp_q_id = "d7472d51b2cd65a9c6b81da09854efdeeeff8afcda1a2934566f54b731a922f3"
    assert q.query_id.hex() == exp_q_id

    # Chain ID, address, and calldata for a fake read function with two arguments
    # (address,uint256)
    q2 = EVMCall(
        chainId=1,
        contractAddress="0x6b175474e89094c44da98b954eedeac495271d0f",
        calldata=bytes.fromhex(
            "a9059cbb0000000000000000000000003f5047bdb647dc39c88625e17bdbffee905a"
            "9f4400000000000000000000000000000000000000000000011c9a62d04ed0c80000"
        ),
    )
    q_data2 = (
        "000000000000000000000000000000000000000000000000000000000000004"
        "0000000000000000000000000000000000000000000000000000000000000008"
        "0000000000000000000000000000000000000000000000000000000000000000"
        "745564d43616c6c0000000000000000000000000000000000000000000000000"
        "000000000000000000000000000000000000000000000000000000000000000e"
        "00000000000000000000000000000000000000000000000000000000000000001"
        "0000000000000000000000006b175474e89094c44da98b954eedeac495271d0f0"
        "00000000000000000000000000000000000000000000000000000000000006000"
        "00000000000000000000000000000000000000000000000000000000000044a90"
        "59cbb0000000000000000000000003f5047bdb647dc39c88625e17bdbffee905a"
        "9f4400000000000000000000000000000000000000000000011c9a62d04ed0c80"
        "00000000000000000000000000000000000000000000000000000000000"
    )
    q_id2 = "0be1ec9e2f8d903de70714f0097d8120ddb9821771d9725c74ae4a99b11714a9"

    assert q2.query_data.hex() == q_data2
    assert q2.query_id.hex() == q_id2


def test_evm_call_get_query_from_data():
    """Test get_query_from_data."""
    q = EVMCall(
        chainId=1,
        contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata=b"\x18\x16\x0d\xdd",
    )
    q2 = EVMCall.get_query_from_data(q.query_data)
    assert q2.query_data == q.query_data
    assert isinstance(q2, EVMCall)


def test_encode_decode_reported_val():
    _ = EVMCall(
        chainId=1,
        contractAddress="0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
        calldata=b"\x18\x16\x0d\xdd",
    )
    pass
    # expected response type is bytes
    # example response of encoded uint256:
    # print(q.value_type.encode(420 * 10 ** 18))
    # print(420 * 10 ** 18)
    # encoded_int = encode_abi(["uint256"], [420 * 10 ** 18])
    # assert encoded_int == bytes.fromhex("000000000000000000000000000000000000000000000016c4abbebea0100000")
    # assert q.value_type.encode(encoded_int) == expected_rsp
    # assert q.value_type.decode(expected_rsp) == encoded_int

    # So in solidity you're assuming that the response will be encoded immediately to bytes
    # or else we'd need to know the type of the response to decode it

    # To do:
    # 1. fix the dataspec query data & id
    # 2. deploy a contract fixture, get its address and calldata for one of its read functions
    # 3. create instance of EVMCall query with the address and calldata
    # 4. call the function using the calldata and address like so:
    # from web3 import Web3

    # # Connect to an Ethereum client
    # w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

    # # The contract address
    # contract_address = '0x1234567890123456789012345678901234567890'

    # # The function signature of the read function (can be obtained using a tool like Remix)
    # function_signature = '0x12345678'

    # # The arguments to pass to the read function
    # arguments = [42]

    # # Encode the arguments using `Web3.codec.encode_abi`
    # encoded_arguments = w3.codec.encode_abi(['uint256'], arguments)

    # # Combine the function signature and the encoded arguments to form the calldata
    # calldata = function_signature + encoded_arguments[2:]

    # # Call the contract's read function using `Web3.eth.call`
    # result = w3.eth.call(
    #     {'to': contract_address, 'data': calldata},
    #     'latest'
    # )

    # 5. try encoding / decoding "result" with the query instance
    # 6. Rewrite steps above as a datasouce and datafed, test separately
