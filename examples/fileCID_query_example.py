"""Text Query Example """
from telliot_feeds.queries.fileCID import FileCIDQuery

q = FileCIDQuery(url="https://gateway.lighthouse.storage/ipfs/QmNVoZntCBiHq1PEqd1J31Ywy4crjVAVYFbMWMGUN2L3Lg")
print(q.descriptor)
print(f"tipQuery data: 0x{q.query_data.hex()}")
print(f"tipQuery ID: 0x{q.query_id.hex()}")

value = "QmNVoZntCBiHq1PEqd1J31Ywy4crjVAVYFbMWMGUN2L3Lg"
print(f"submitValue (str): {value}")

encoded_bytes = q.value_type.encode(value)
print(f"submitValue (bytes): 0x{encoded_bytes.hex()}")

decoded_value = q.value_type.decode(encoded_bytes)
print(f"Decoded value (float): {decoded_value}")
