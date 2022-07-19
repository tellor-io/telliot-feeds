"""Legacy Query Example """
from telliot_feeds.queries import LegacyRequest

q = LegacyRequest(legacy_id=1)
print(q.descriptor)
print(f"tipQuery data: 0x{q.query_data.hex()}")
print(f"tipQuery ID: 0x{q.query_id.hex()}")

value = 10000.1234567
print(f"submitValue (float): {value}")

encoded_bytes = q.value_type.encode(value)
print(f"submitValue (bytes): 0x{encoded_bytes.hex()}")

decoded_value = q.value_type.decode(encoded_bytes)
print(f"Decoded value (float): {decoded_value}")
