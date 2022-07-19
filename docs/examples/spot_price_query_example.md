# Spot Price Query Example

This example demonstrates how to use the
[`SpotPrice`][telliot_feeds.queries.price.spot_price.SpotPrice] Oracle query.

## Create the query

Create a [`SpotPrice`][telliot_feeds.queries.price.spot_price.SpotPrice] query for the price of Bitcoin in US dollars,
and view the corresponding descriptor::

```python
from telliot_feeds.queries.price.spot_price import SpotPrice
q = SpotPrice(asset='btc', currency='usd')
print(q.descriptor)
```

The query `.descriptor` attribute returns a unique string that identifies this query to the
TellorX Oracle network:

```json
{ "type": "SpotPrice", "asset": "btc", "currency": "usd" }
```

## On-chain representation

To make the corresponding on-chain Query request,
the `TellorX.Oracle.tipQuery()` contract call
requires two arguments: `queryData` and `queryId`. These arguments are computed solely from the
query `descriptor`, and are provided by
the `query_data` and `query_id` attributes as a convenience.

```python
print(f"tipQuery data: 0x{q.query_data.hex()}")
print(f"tipQuery ID: 0x{q.query_id.hex()}")
```

which, for this example, are:

    tipQuery data: 0x7b2274797065223a2253706f745072696365222c226173736574223a22627463222c2263757272656e6379223a22757364227d
    tipQuery ID: 0xd66b36afdec822c56014e56f468dee7c7b082ed873aba0f7663ec7c6f25d2c0a

## Response encoding/decoding

The `SpotPrice` query can also be used to encode a response
to submit on-chain using the `TellorX.Oracle.submitValue()` contract call.

For example, to submit the real world value `99.9` use the
[`ValueType`][telliot_feeds.dtypes.value_type.ValueType].[`encode`][telliot_feeds.dtypes.value_type.ValueType.encode]
method.

```python
value = 99.99
print(f"submitValue (float): {value}")
encoded_bytes = q.value_type.encode(value)
print(f"submitValue (bytes): 0x{encoded_bytes.hex()}")
```

    submitValue (float): 99.99
    submitValue (bytes): 0x0000000000000000000000000000000000000000000000056ba3d73af34eec04

Similarly, the
[`decode`][telliot_feeds.dtypes.value_type.ValueType.decode] method can be used to convert
the on-chain bytes value to a real-world value:

```python
decoded_value = q.value_type.decode(encoded_bytes)
print(f"Decoded value (float): {decoded_value}")
```

    Decoded value (float): 99.99

## Full Example

The full example is provided here for reference

```python
--8<-- "examples/text_query_example.py"
```
