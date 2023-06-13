# Helper functions used for reporter tests
from telliot_core.utils.response import ResponseStatus


async def gas_price(speed="average"):
    return 1


async def passing_status(*args, **kwargs):
    return ResponseStatus()


async def passing_bool_w_status(*args, **kwargs):
    return True, ResponseStatus()


def chain_time(chain):
    return round(chain.time())
