import requests

rsp = requests.get("https://api.bitflyer.com/v1/markets")
print(rsp.status_code)
print(rsp.json())
