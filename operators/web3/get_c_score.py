import logging
from datetime import datetime, timedelta

import aiohttp

from echelon.common.config import SETTINGS
from echelon.common.utils import score
from echelon.operators.web3.bscan_api import base_query_score
from echelon.operators.web3.escan_api import etherscan_query_score
from echelon.operators.web3.sscan_api import solana_query_score

logger = logging.getLogger(__name__)


async def get_crypto_platform_score(contract_address=None, platform=None):
    if not contract_address or not isinstance(platform, dict):
        return None
    platform_name = platform.get("slug", "")
    if platform_name not in ["ethereum", "solana", "base"]:
        return None

    if "ethereum" == platform_name:
        return await etherscan_query_score(contract_address)
    elif "solana" == platform_name:
        return await solana_query_score(contract_address)
    elif "base" == platform_name:
        return await base_query_score(contract_address)


async def get_historical_data(symbol: str):
    url = f"{SETTINGS.C_PRO_BASE_URL}/v1/cryptocurrency/ohlcv/historical"
    headers = {
        'X-CMC_PRO_API_KEY': SETTINGS.C_PRO_API_KEY,
        'Accept': 'application/json',
    }

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(2)

    end_timestamp = int(end_time.timestamp())
    start_timestamp = int(start_time.timestamp())

    params = {
        'symbol': symbol,
        'time_start': start_timestamp,
        'time_end': end_timestamp,
        'time_period': 'hourly',
        'interval': 'hourly',
        'convert': 'USD',
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    ohlcv_data = data['data']['quotes']
                    return ohlcv_data
        except aiohttp.ClientError as e:
            logger.error(f"Failed to get historical data: {params}")
    return None


async def get_crypto_symbol_score(symbol=None):
    if not symbol:
        return 0.0, 0.0

    ohlcv_data = await get_historical_data(symbol)
    if not isinstance(ohlcv_data, list) or len(ohlcv_data) < 2:
        return 0.0, 0.0

    volume_score = 0.0
    market_cap_score = 0.0

    try:
        prev_data = ohlcv_data[0]
        current_data = ohlcv_data[1]

        prev_volume = prev_data['quote']['USD']['volume']
        current_volume = current_data['quote']['USD']['volume']
        volume_score = score(prev_volume, current_volume)

        prev_market_cap = prev_data['quote']['USD']['market_cap']
        current_market_cap = current_data['quote']['USD']['market_cap']
        market_cap_score = score(prev_market_cap, current_market_cap)
    except Exception as e:
        logger.error(f"Failed to get historical data: {symbol}")
    return volume_score, market_cap_score
