from binance.client import Client

api_key = "xxx"
api_secret = "xxx"

client = Client()
exchange_info = client.get_exchange_info()
for s in exchange_info["symbols"]:
    print(s["symbol"])
