"""Utils for Telliot Reporter classes"""

import requests

async def is_online() -> bool:
    try:
        await requests.get('http://1.1.1.1')
        return True
    except requests.exceptions.ConnectionError:
        return False