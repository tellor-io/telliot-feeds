"""Utils for Telliot Reporter classes"""
import requests


async def is_online() -> bool:
    """checks internet connection by pinging Cloudflare DNS"""
    try:
        requests.get("http://1.1.1.1")
        return True
    except requests.exceptions.ConnectionError:
        return False
