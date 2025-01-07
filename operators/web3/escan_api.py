import logging
import time

import aiohttp

from echelon.common.config import SETTINGS
from echelon.common.utils import score

logger = logging.getLogger(__name__)

BASE_URL = SETTINGS.E_BASE_URL


async def get_block_by_timestamp(timestamp):
    try:
        url = f"{BASE_URL}?module=block&action=getblocknobytime&timestamp={timestamp}&closest=before&apikey={SETTINGS.E_API_KEY}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                return data['result']
    except Exception as error:
        logger.error(error)

    return None


async def get_erc20_token_transfer_events(contract_address, start_block, end_block):
    url = f"{BASE_URL}?module=account&action=tokentx&contractaddress={contract_address}&startblock={start_block}&endblock={end_block}&sort=asc&apikey={SETTINGS.E_API_KEY}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                print("block-data", data)
                if data['status'] == '1':
                    return data['result']
                else:
                    return []
    except Exception as error:
        logger.error(error)
    return None


async def etherscan_query_score(contract_address: str):
    hour = 1
    start_time = int(time.time()) - hour * 60 * 60
    end_time = int(time.time())
    start_block = await get_block_by_timestamp(start_time)
    if not start_block:
        return 0.0
    end_block = await get_block_by_timestamp(end_time)
    if not end_block:
        return 0.0

    half_time = (start_time + end_time) // 2
    half_block = get_block_by_timestamp(half_time)

    start_txns = await get_erc20_token_transfer_events(contract_address, start_block, half_block)
    if not start_txns:
        return 0.0
    end_txns = await get_erc20_token_transfer_events(contract_address, half_block, end_block)
    if not end_txns:
        return 0.0

    return score(len(start_txns), len(end_txns))
