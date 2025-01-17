"""Text Query Example """
from telliot_feeds.queries.grip_dyno_challenge_query import EthDenverChallenge2025

q = EthDenverChallenge2025(challengeType="grip_strength_dynometer")
print(f"Challenge Type: {q.challengeType}")

print(f"QueryData: 0x{q.query_data.hex()}")
print(f"QueryID: 0x{q.query_id.hex()}")

value = (
    True,  # data_set
    123.56,  # right_hand
    34.51,  # left_hand
    "0xSpuddy",  # x_handle
    "0xSpuddy",  # github_username
    3,  # hours_of_sleep
)
print(f"submitValue: {value}")

encoded_bytes = q.value_type.encode(value)
print(f"submitValue (bytes): 0x{encoded_bytes.hex()}")

decoded_value = q.value_type.decode(encoded_bytes)
print(f"Decoded value (float): {decoded_value}")
