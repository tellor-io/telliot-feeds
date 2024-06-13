"""Text Query Example """
from telliot_feeds.queries.snapshot import Snapshot

q = Snapshot(
    proposalId="bafybeic4eycnfgz6kstnai27m3cwda5rkrtsktdmzenld6m4vufgzoze3m",
    transactionsHash="0x6f49a2f0da92ef653ba883aa21b2e3ff4d3350080b5627db6eba68b45eae1fd7",
    moduleAddress="0xB1bB6479160317a41df61b15aDC2d894D71B63D9",
)

query_data = q.query_data

print(q.descriptor)
print(f"tipQuery data: 0x{q.query_data.hex()}")
print(f"tipQuery ID: 0x{q.query_id.hex()}")

value = True
print(f"submitValue (bool): {value}")

encoded_bytes = q.value_type.encode(value)
print(f"submitValue (bool): 0x{encoded_bytes.hex()}")

decoded_value = q.value_type.decode(encoded_bytes)
print(f"Decoded value (bool): {decoded_value}")
