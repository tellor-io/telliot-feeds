# Text Query Example

The following example demonstrates how to create a
[`StringQuery`][telliot_feeds.queries.string_query.StringQuery] request.

Create a `StringQuery` and view the corresponding query descriptor::

```python hl_lines="4-5"
--8<-- "examples/text_query_example.py"
```

The query descriptor string uniquely identifies this query to the
TellorX Oracle network.

```json
{ "type": "StringQuery", "text": "What is the meaning of life?" }
```

To make the corresponding on-chain Query request,
the `TellorX.Oracle.tipQuery()` contract call
requires two arguments: `queryData` and `queryId`. These arguments are provided by
the `query_data` and `query_id` attributes of the `StringQuery` object:

```python hl_lines="6 7"
--8<-- "examples/text_query_example.py"
```

which, for this example, are:

    tipQuery data: 0x7b2274797065223a22537472696e675175657279222c2274657874223a225768617420697320746865206d65616e696e67206f66206c6966653f227d
    tipQuery ID: 0xdd349fc565b13987a11bed4cc9e7382863491638769020afad1abe3840ec14b7

The `StringQuery` object also demonstrates how to encode a response
to submit on-chain using the `TellorX.Oracle.submitValue()` contract call.

For example, to submit following the answer

    Please refer to: https://en.wikipedia.org/wiki/Meaning_of_life

use the
[`encode`][telliot_feeds.dtypes.value_type.ValueType.encode] and
[`decode`][telliot_feeds.dtypes.value_type.ValueType.decode] methods of the response
[`ValueType`][telliot_feeds.dtypes.value_type.ValueType].

```python hl_lines="9-16"
--8<-- "examples/text_query_example.py"
```

Note that the on-chain and decoded values are limited to
6 decimals of precision in accordance with the on-chain data type:

    submitValue (str): Please refer to: https://en.wikipedia.org/wiki/Meaning_of_life
    submitValue (bytes): 0x000000000000000000000000000000000000000000000000000000000000003e506c6561736520726566657220746f3a2068747470733a2f2f656e2e77696b6970656469612e6f72672f77696b692f4d65616e696e675f6f665f6c6966650000
    Decoded value (float): Please refer to: https://en.wikipedia.org/wiki/Meaning_of_life
