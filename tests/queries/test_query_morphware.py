""" Unit tests for Morphware queries.

Copyright (c) 2021-, Tellor Development Community
Distributed under the terms of the MIT License.
"""
import json

from eth_abi import decode_abi
from eth_abi import decode_single

from telliot_feeds.queries.morphware import Morphware


def test_query_constructor():
    """Validate Morphware query."""
    q = Morphware(version=1)

    exp_query_data = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\tMorphwar"
        b"e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x01"
    )

    assert q.query_data == exp_query_data

    query_type, encoded_param_vals = decode_abi(["string", "bytes"], q.query_data)
    assert query_type == "Morphware"

    version = decode_single("uint256", encoded_param_vals)
    assert isinstance(version, int)
    assert version == 1

    exp = "bf7f9942188d84961cf2a01ec68c42ef000d5b0fb5ca7dc0fcf1ceee5164811c"
    assert q.query_id.hex() == exp


def test_encode_decode_reported_val():
    """Ensure expected encoding/decoding behavior."""
    q = Morphware(version=1)

    # JSON string containing data specified by Morphware and
    # referenced in Tellor /dataSpecs:
    # https://github.com/tellor-io/dataSpecs/blob/main/types/Morphware.md

    # Example data source provided by Morphware:
    # curl --request POST http://167.172.239.133:5000/products-2 -H "Content-Type: application/json" \
    # -d '{"provider":"amazon","service":"compute","region":"us-east-1"}'
    data_from_endpoint = [
        {
            "Instance Type": "p2.16xlarge",
            "CUDA Cores": 79872,
            "Number of CPUs": 64,
            "RAM": 732.0,
            "On-demand Price per Hour": 14.4,
        },
        # ...
    ]
    # Rename needed fields
    data = [
        {
            "instanceType": data_from_endpoint[0]["Instance Type"],
            "cudaCores": data_from_endpoint[0]["CUDA Cores"],
            "numCPUs": data_from_endpoint[0]["Number of CPUs"],
            "RAM": data_from_endpoint[0]["RAM"],
            "onDemandPricePerHour": data_from_endpoint[0]["On-demand Price per Hour"],
        }
    ]
    # Convert Ec2Metadata to JSON string
    data = [json.dumps(data[0])]

    submit_value = q.value_type.encode(data)
    assert isinstance(submit_value, bytes)

    decoded_data = q.value_type.decode(submit_value)
    assert isinstance(decoded_data, tuple)
    assert isinstance(decoded_data[0], str)

    d = json.loads(decoded_data[0])
    assert d["instanceType"] == "p2.16xlarge"
    assert d["onDemandPricePerHour"] == 14.4
