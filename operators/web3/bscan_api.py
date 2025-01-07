import logging
import time

import aiohttp

from echelon.common.config import SETTINGS
from echelon.common.utils import score

logger = logging.getLogger(__name__)


async def get_block_by_timestamp(timestamp: int) -> int:
    params = {
        "module": "block",
        "action": "getblocknobytime",
        "timestamp": timestamp,
        "closest": "before",
        "apikey": SETTINGS.B_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(SETTINGS.B_API_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "1":
                        return int(data["result"])
    except Exception as e:
        logger.error(e)
    return None


async def get_tx_list_in_block_range(
        contract_address: str,
        start_block: int,
        end_block: int,
) -> list:
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": contract_address,
        "startblock": start_block,
        "endblock": end_block,
        "sort": "asc",
        "apikey": SETTINGS.B_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(SETTINGS.B_API_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "1":
                        return data["result"]
    except Exception as e:
        logger.error(e)
    return None


async def base_query_score(contract_address: str) -> float:
    hour = 1
    end_time = int(time.time())
    mid_time = end_time - hour * 60 * 60
    start_time = mid_time - hour * 60 * 60

    start_block = await get_block_by_timestamp(start_time)
    if not start_block:
        return 0.0
    end_block = await get_block_by_timestamp(end_time)
    if not end_block:
        return 0.0
    mid_block = await get_block_by_timestamp(mid_time)
    if not mid_block:
        return 0.0

    start_block, end_block = min(start_block, end_block), max(start_block, end_block)

    txs_first_half = await get_tx_list_in_block_range(contract_address, start_block, mid_block - 1)
    if not txs_first_half:
        return 0.0
    txs_second_half = await get_tx_list_in_block_range(contract_address, mid_block, end_block)
    if not txs_second_half:
        return 0.0

    return score(len(txs_first_half), len(txs_second_half))
