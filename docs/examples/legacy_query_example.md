# Legacy Query Example

This example demonstrates how to create a
[`LegacyRequest`][telliot_feeds.queries.legacy_query.LegacyRequest]
requesting the ETH/USD price. The legacy request ID for ETH/USD is `1`,
in accordance with the
[Legacy Data Feed ID Specifications](https://docs.tellor.io/tellor/integration/data-ids/current-data-feeds).

## Create the query

Create a LegacyQuery and view the corresponding query descriptor:

```python
from telliot_feeds.queries import LegacyRequest
q = LegacyRequest(legacy_id=1)
print(q.descriptor)
```

The query descriptor string uniquely identifies this query to the
TellorX Oracle network.

```json
{ "type": "LegacyRequest", "legacy_id": 1 }
```

## On-chain representation

To make the corresponding on-chain Query request,
the `TellorX.Oracle.tipQuery()` contract call
requires two arguments: `queryData` and `queryId`. These arguments are provided by
the `query_data` and `query_id` attributes of the `LegacyQuery` object:

```python
print(f"tipQuery data: 0x{q.query_data.hex()}")
print(f"tipQuery ID: 0x{q.query_id.hex()}")
```

which, for this example, are:

    tipQuery data: 0x7b2274797065223a224c656761637952657175657374222c226c65676163795f6964223a317d
    tipQuery ID: 0x0000000000000000000000000000000000000000000000000000000000000001

## Response encoding/decoding

The `LegacyQuery` object also demonstrates how to encode a response
to submit on-chain using the `TellorX.Oracle.submitValue()` contract call.

For example, to submit the value `10000.1234567`, use the
[`encode`][telliot_feeds.dtypes.value_type.ValueType.encode] and
[`decode`][telliot_feeds.dtypes.value_type.ValueType.decode] methods of the response
[`ValueType`][telliot_feeds.dtypes.value_type.ValueType].

```python
value = 10000.1234567
print(f"submitValue (float): {value}")
encoded_bytes = q.value_type.encode(value)
print(f"submitValue (bytes): 0x{encoded_bytes.hex()}")
```

Note that the on-chain and decoded values are limited to
6 decimals of precision in accordance with the on-chain data type:

    submitValue (float): 10000.1234567
    submitValue (bytes): 0x00000000000000000000000000000000000000000000000000000002540dc641

Similarly, the
[`decode`][telliot_feeds.dtypes.value_type.ValueType.decode] method can be used to convert
the on-chain bytes value to a real-world value:

```python
decoded_value = q.value_type.decode(encoded_bytes)
print(f"Decoded value (float): {decoded_value}")
```

    Decoded value (float): 10000.123457

## Full Example

The full example is provided here for reference

```python
--8<-- "examples/legacy_query_example.py"
```
