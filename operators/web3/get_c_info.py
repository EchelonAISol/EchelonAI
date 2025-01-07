import logging
from typing import Optional, Dict

import aiohttp
from pydantic import BaseModel

from echelon.common.codec import jsondumps
from echelon.common.config import SETTINGS
from echelon.operators.web3 import CmcOp

logger = logging.getLogger(__name__)


class GetCryptoInfoReq(BaseModel):
    symbol_or_address: Optional[str] = None
    symbol: Optional[str] = None
    address: Optional[str] = None


class CryptoInfo(BaseModel):
    status: Optional[Dict] = None
    data: Optional[Dict] = None


class GetCryptoInfo(CmcOp):
    url: str = f"{SETTINGS.C_PRO_BASE_URL}/v2/cryptocurrency/info"

    async def call(self, input: GetCryptoInfoReq = None) -> Optional[CryptoInfo]:
        if input and not input.symbol_or_address:
            return await super().call(input)
        try:
            ret = await super().call(GetCryptoInfoReq(address=input.symbol_or_address))
            if ret:
                return ret
            return await super().call(GetCryptoInfoReq(symbol=input.symbol_or_address))
        except Exception as e:
            logger.error(e)
        return None

    async def _to_resp(self, json: dict) -> Optional[CryptoInfo]:
        ret = None
        if json and isinstance(json.get("data", None), dict):
            logger.info(f"GetCryptoInfo got json: {jsondumps(json)}")
            ret = CryptoInfo(**json)
        return ret


class GetCryptoInfoV2:

    async def call(self, ca: str = None) -> dict[str, str]:
        platform = None
        ret = await self._do_call(chain="ether", ca=ca)
        if ret:
            platform = "ether"
        else:
            ret = await self._do_call(chain="solana", ca=ca)
            if ret:
                platform = "solana"
            else:
                ret = await self._do_call(chain="base", ca=ca)
                if ret:
                    platform = "base"
                else:
                    ret = await self._do_call(chain="tron", ca=ca)
                    if ret:
                        platform = "tron"
        if platform:
            return {"platform": platform, "symbol": ret}
        return None

    async def _do_call(self, chain: str, ca: str = None) -> str:
        headers = {
            "X-API-Key": f"{SETTINGS.D_API_KEY}",
            "accept": "application/json",
            "User-Agent": "API-Wrapper/0.3"
        }
        url = f"{SETTINGS.D_BASE_URL}/trial/v2/token/{chain}/{ca}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            logger.info(f"GetCryptoInfoV2 got json: {jsondumps(data)}")
                            symbol = data.get("data", {}).get("symbol")
                            return symbol
                    else:
                        return None
        except Exception as e:
            logger.error(f"GetCryptoInfoV2 got exception: {ca}")
        return None
