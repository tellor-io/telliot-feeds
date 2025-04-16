"""Text Query Example """
from telliot_feeds.queries.grip_dyno_challenge_query import EthDC2025Test

q = EthDC2025Test(challengeType="grip_strength_dynamometer")
print(f"Challenge Type: {q.challengeType}")

print(f"QueryData: 0x{q.query_data.hex()}")
print(f"QueryID: 0x{q.query_id.hex()}")

value = (
    True,  # data_set
    109,  # right_hand
    114.52,  # left_hand
    "0xspuddy_x",  # x_handle
    "0xspuddy_git",  # github_username
    4,  # hours_of_sleep
)
print(f"submitValue: {value}")

encoded_bytes = q.value_type.encode(value)
print(f"submitValue (bytes): 0x{encoded_bytes.hex()}")

decoded_value = q.value_type.decode(encoded_bytes)
