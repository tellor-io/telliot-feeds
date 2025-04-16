"""Text Query Example """
from telliot_feeds.queries.grip_dyno_challenge_query import EthDc2025Test2

q = EthDc2025Test2(challengeType="grip_strength_dynamometer")
print(f"Challenge Type: {q.challengeType}")

print(f"QueryData: 0x{q.query_data.hex()}")
print(f"QueryID: 0x{q.query_id.hex()}")

value = (
    True,  # data_set
    1,  # right_hand
    1,  # left_hand
    "spuddy_test",  # cypherpunk_name
)
print(f"submitValue: {value}")

encoded_bytes = q.value_type.encode(value)
print(f"submitValue (bytes): 0x{encoded_bytes.hex()}")

decoded_value = q.value_type.decode(encoded_bytes)
