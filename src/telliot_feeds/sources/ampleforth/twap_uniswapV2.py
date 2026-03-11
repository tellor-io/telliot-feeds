from datetime import datetime, timedelta, timezone
from web3 import Web3
import asyncio


AMPL_WETH_PAIR = Web3.to_checksum_address("0xc5be99A02C6857f9Eac67BbCE58DF5572498F40c")

WETH_USDC_PAIR = Web3.to_checksum_address("0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc")

Q112 = 2 ** 112

PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "price0CumulativeLast",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "price1CumulativeLast",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"},
        ],
        "type": "function",
    },
]

AMPL_ADDRESS = Web3.to_checksum_address("0xD46bA6D942050d489DBd938a2C909A5d5039A161")

AMPL_DECIMALS = 9
WETH_DECIMALS = 18
USDC_DECIMALS = 6


async def find_block_by_timestamp(w3: Web3, target_ts: int, latest_block: dict) -> int:

    
    latest_num = latest_block["number"]
    latest_ts = latest_block["timestamp"]

    if target_ts >= latest_ts:
        return latest_num

    # Estimate block using ~12s per block
    seconds_ago = latest_ts - target_ts
    estimated_block = max(1, latest_num - (seconds_ago // 12))

    # Search 2000 blocks above and below our estimate, just in case it's off
    min_block = max(1, estimated_block - 2000)
    max_block = min(latest_num, estimated_block + 2000)


    lo_data = w3.eth.get_block(min_block)
    if target_ts < lo_data["timestamp"]:
        min_block = 1

    hi_data = w3.eth.get_block(max_block)
    if target_ts > hi_data["timestamp"]:
        max_block = latest_num

    while min_block < max_block:
        mid = (min_block + max_block + 1) // 2
        mid_block = w3.eth.get_block(mid)
        if mid_block["timestamp"] <= target_ts:
            min_block = mid
        else:
            max_block = mid - 1

    return min_block

async def get_true_cumulative_price(pair_contract, block_number: int, w3: Web3):
    cum0 = pair_contract.functions.price0CumulativeLast().call(
        block_identifier=block_number
    )
    cum1 = pair_contract.functions.price1CumulativeLast().call(
        block_identifier=block_number
    )
    reserves = pair_contract.functions.getReserves().call(
        block_identifier=block_number
    )
    reserve0, reserve1, ts_last_update = reserves

    block = w3.eth.get_block(block_number)
    block_ts = block["timestamp"]

    time_elapsed = (block_ts - ts_last_update) % (2 ** 32)

    if time_elapsed > 0 and reserve0 > 0 and reserve1 > 0:
        cum0 += (reserve1 * Q112 // reserve0) * time_elapsed
        cum1 += (reserve0 * Q112 // reserve1) * time_elapsed

    return cum0, cum1, block_ts

async def compute_pair_twap(w3: Web3, pair_address, block_start: int, block_end: int,
                      use_price0: bool, decimal_adjustment: float = 1.0):

    pair = w3.eth.contract(address=pair_address, abi=PAIR_ABI)

    cum0_start, cum1_start, ts_start = await get_true_cumulative_price(pair, block_start, w3)
    cum0_end, cum1_end, ts_end = await get_true_cumulative_price(pair, block_end, w3)

    actual_elapsed = ts_end - ts_start
    if actual_elapsed == 0:
        raise ValueError("Start and end blocks have the same timestamp.")

    if use_price0:
        cum_diff = cum0_end - cum0_start
    else:
        cum_diff = cum1_end - cum1_start

    twap_uq112 = cum_diff // actual_elapsed
    twap_raw = twap_uq112 / Q112

    twap = twap_raw * decimal_adjustment

    return twap

async def compute_twap(start_timestamp: int, end_timestamp: int, w3: Web3):
    if not w3.is_connected():
        raise ConnectionError("Cannot connect to RPC. Check your API key.")

    pair = w3.eth.contract(address=AMPL_WETH_PAIR, abi=PAIR_ABI)

    token0 = pair.functions.token0().call()


    latest = w3.eth.get_block("latest")
    if end_timestamp > latest["timestamp"]:
        raise ValueError(
            f"day has not ended yet. Latest block timestamp: "
            f"{datetime.fromtimestamp(latest['timestamp'], tz=timezone.utc).isoformat()}"
        )
    latest = w3.eth.get_block("latest")
    block_start = await find_block_by_timestamp(w3, start_timestamp, latest)

    if w3.eth.get_block(block_start)["timestamp"] < start_timestamp:
        block_start += 1
    block_end = await find_block_by_timestamp(w3, end_timestamp, latest)

    ampl_weth_decimal_adj = 10 ** (AMPL_DECIMALS - WETH_DECIMALS)  # 10^(-9)
    ampl_per_weth_decimal_adj = 10 ** (WETH_DECIMALS - AMPL_DECIMALS)  # 10^9

    if token0.lower() == AMPL_ADDRESS.lower():
        # price0 = token1/token0 = WETH/AMPL
        ampl_weth_use_price0 = True
    else:
        # price1 = token0/token1 = WETH/AMPL
        ampl_weth_use_price0 = False

    twap_weth_per_ampl = await compute_pair_twap(
        w3, AMPL_WETH_PAIR, block_start, block_end,
        use_price0=ampl_weth_use_price0,
        decimal_adjustment=ampl_weth_decimal_adj,
    )


    twap_ampl_per_weth = await compute_pair_twap(
        w3, AMPL_WETH_PAIR, block_start, block_end,
        use_price0=(not ampl_weth_use_price0),
        decimal_adjustment=ampl_per_weth_decimal_adj,
    )


    # USDC is token0, WETH is token1
    eth_usd_decimal_adj = 10 ** (WETH_DECIMALS - USDC_DECIMALS)  # 10^12

    eth_usd_twap = await compute_pair_twap(
        w3, WETH_USDC_PAIR, block_start, block_end,
        use_price0=False,
        decimal_adjustment=eth_usd_decimal_adj,
    )

    ampl_usd = twap_weth_per_ampl * eth_usd_twap

    print({
        "twap_weth_per_ampl": twap_weth_per_ampl,
        "twap_ampl_per_weth": twap_ampl_per_weth,
        "eth_usd_twap": eth_usd_twap,
        "ampl_usd": ampl_usd,
        "block_start": block_start,
        "block_end": block_end,
    })
    return ampl_usd

if __name__ == "__main__":
    ALCHEMY_API_KEY = "key"
    RPC_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"


    target_date = datetime.now(timezone.utc).date() - timedelta(days=1)
    day_start_dt = datetime(
        target_date.year, target_date.month, target_date.day,
        0, 0, 0, tzinfo=timezone.utc
    )
    day_end_dt = datetime(
        target_date.year, target_date.month, target_date.day,
        23, 59, 59, tzinfo=timezone.utc
    )
    start_timestamp = int(day_start_dt.timestamp())
    end_timestamp = int(day_end_dt.timestamp())
    result = asyncio.run(compute_twap(start_timestamp, end_timestamp, Web3(Web3.HTTPProvider(RPC_URL))))
    print(f"AMPL/USD TWAP for {target_date.isoformat()}: {result}")