import logging
from datetime import datetime, timedelta

import aiohttp

from echelon.common.config import SETTINGS
from echelon.common.utils import score

logger = logging.getLogger(__name__)

BITQUERY_URL = SETTINGS.BQ_BASE_URL
GRAPHQL_QUERY_TEMPLATE = {
    "ethereum": """
    query ($address: String!, $startTime: ISO8601DateTime!, $endTime: ISO8601DateTime!) {
      ethereum(network: ethereum) {
        transfers(
          currency: {is: $address}
          date: {between: [$startTime, $endTime]}
        ) {
          count
        }
      }
    }
    """,
    "solana": """
    query ($address: String!, $startTime: ISO8601DateTime!, $endTime: ISO8601DateTime!) {
      solana(network: solana) {
        transfers(
          currency: {is: $address}
          date: {between: [$startTime, $endTime]}
        ) {
          count
        }
      }
    }
    """,
    "base": """
    query ($address: String!, $startTime: ISO8601DateTime!, $endTime: ISO8601DateTime!) {
      base(network: base) {
        transfers(
          currency: {is: $address}
          date: {between: [$startTime, $endTime]}
        ) {
          count
        }
      }
    }
    """
}


async def execute_bitquery(chain, contract_address, start_time, end_time):
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": SETTINGS.BQ_API_KEY
    }

    try:
        query = GRAPHQL_QUERY_TEMPLATE.get(chain)
        if not query:
            return None

        variables = {
            "address": contract_address,
            "startTime": start_time,
            "endTime": end_time
        }

        payload = {
            "query": query,
            "variables": variables
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(BITQUERY_URL, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise ConnectionError(f"Query failed with status code {response.status}: {await response.text()}")
                result = await response.json()
                return int(result["data"][chain]["transfers"][0]["count"])
    except Exception as e:
        logger.error(f"Error executing bitquery for chain {chain}: {e}")
    return None


def get_time_range(delta_hours_start, delta_hours_end):
    end_time = datetime.utcnow() - timedelta(hours=delta_hours_start)
    start_time = datetime.utcnow() - timedelta(hours=delta_hours_end)
    return start_time.isoformat() + "Z", end_time.isoformat() + "Z"


async def solana_query_score(contract_address: str):
    start_time_24h, end_time_24h = get_time_range(0, 24)
    start_time_48h, end_time_48h = get_time_range(24, 48)

    count_24h = await execute_bitquery(
        chain="solana",
        contract_address=contract_address,
        start_time=start_time_24h,
        end_time=end_time_24h
    )
    if not count_24h:
        return 0.0

    count_48h_to_24h = await execute_bitquery(
        chain="solana",
        contract_address=contract_address,
        start_time=start_time_48h,
        end_time=end_time_48h
    )
    if not count_48h_to_24h:
        return 0.0

    return score(count_48h_to_24h, count_24h)
