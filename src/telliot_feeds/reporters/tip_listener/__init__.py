import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from multicall import multicall
from multicall.constants import MULTICALL2_ADDRESSES
from multicall.constants import Network

# from multicall import multicall
# import asyncio
# from concurrent.futures import ThreadPoolExecutor

# add testnet support for multicall that aren't avaialable in the package
Network.Mumbai = 80001
MULTICALL2_ADDRESSES[Network.Mumbai] = "0x35583BDef43126cdE71FD273F5ebeffd3a92742A"
Network.ArbitrumRinkeby = 421611
MULTICALL2_ADDRESSES[Network.ArbitrumRinkeby] = "0xf609687230a65E8bd14caceDEfCF2dea9c15b242"
Network.OptimismKovan = 69
MULTICALL2_ADDRESSES[Network.OptimismKovan] = "0xf609687230a65E8bd14caceDEfCF2dea9c15b242"
Network.PulsechainTestnet = 941
MULTICALL2_ADDRESSES[Network.PulsechainTestnet] = "0x959a437F1444DaDaC8aF997E71EAF0479c810267"


async def run_in_subprocess(coro: Any, *args: Any, **kwargs: Any) -> Any:
    """Use ThreadPoolExecutor to execute tasks"""
    return await asyncio.get_event_loop().run_in_executor(ThreadPoolExecutor(16), coro, *args, **kwargs)


# Multicall interface uses ProcessPoolExecutor which leaks memory and breaks when used for the tip listener
# switching to use ThreadPoolExecutor instead seems to fix that
multicall.run_in_subprocess = run_in_subprocess
