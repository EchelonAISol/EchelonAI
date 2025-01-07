import logging
from typing import Any

import aiohttp

from echelon.common.codec import jsondumps
from echelon.common.config import SETTINGS

logger = logging.getLogger(__name__)


async def get_markets(contract_address=None, platform=None) -> Any:
    if not contract_address or not isinstance(platform, dict):
        return None
    chain = platform.get("slug", "")
    if not chain:
        return None

    headers = {
        "X-API-Key": f"{SETTINGS.D_API_KEY}",
        "accept": "application/json",
        "User-Agent": "API-Wrapper/0.3"
    }
    url = f"{SETTINGS.D_BASE_URL}/trial/v2/token/{chain}/{contract_address}/price"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        logger.info(f"get_markets data: {jsondumps(data)}")
                    return data
                else:
                    return None
    except Exception as e:
        logger.error(e)
    return None


async def get_markets_info(contract_address=None, platform=None) -> Any:
    if not contract_address or not isinstance(platform, dict):
        return None
    chain = platform.get("slug", "")
    if not chain:
        return None

    headers = {
        "X-API-Key": f"{SETTINGS.D_API_KEY}",
        "accept": "application/json",
        "User-Agent": "API-Wrapper/0.3"
    }
    url = f"{SETTINGS.D_BASE_URL}/trial/v2/token/{chain}/{contract_address}/info"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        logger.info(f"get_markets_info data: {jsondumps(data)}")
                    return data
                else:
                    return None
    except Exception as e:
        logger.error(e)
    return None
