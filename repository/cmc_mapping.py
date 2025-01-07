import logging
from typing import Optional

from pydantic import BaseModel

from echelon.operators.web3.get_c_info import GetCryptoInfoReq, GetCryptoInfo, GetCryptoInfoV2

logger = logging.getLogger(__name__)


class CmcCrypto(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    symbol: Optional[str] = None
    urls: Optional[dict] = None
    platform: Optional[dict] = None
    ca: Optional[str] = None


CMC_MAPPING: dict[str, dict] = {}


async def get_crypto_mapping(key: str) -> Optional[CmcCrypto]:
    try:
        m = CMC_MAPPING.get(key, None)
        if m:
            logger.info(f"crypto mapping keys: {list(CMC_MAPPING.keys())}")
            return m
        ret = await GetCryptoInfo().call(GetCryptoInfoReq(symbol_or_address=key))
        temp = None
        if ret and ret.data:
            for d in ret.data.values():
                if isinstance(d, dict):
                    rrr = CmcCrypto(**d)
                    rrr.ca = key
                    CMC_MAPPING[key] = rrr
                if isinstance(d, list):
                    for item in d:
                        if isinstance(item, dict):
                            if item.get("category") == 'coin':
                                r = CmcCrypto(**item)
                                r.ca = key
                                CMC_MAPPING[key] = r
                            elif item.get("category") == 'token':
                                contract_address = item.get('contract_address', [])
                                if contract_address and len(contract_address) > 0:
                                    ca = contract_address[0].get('contract_address', None)
                                    if ca:
                                        rr = CmcCrypto(**item)
                                        rr.ca = ca
                                        CMC_MAPPING[ca] = rr
                                        temp = rr

        cached = CMC_MAPPING.get(key, None)
        if not cached and ret and ret.data and temp:
            return temp

        if not cached:
            v2 = await GetCryptoInfoV2().call(ca=key)
            if isinstance(v2, dict):
                v2_r = CmcCrypto()
                v2_r.symbol = v2.get('symbol', "")
                v2_r.ca = key
                v2_r.platform = {"slug": v2.get('platform', "")}
                CMC_MAPPING[key] = v2_r
        logger.info(f"crypto mapping keys: {list(CMC_MAPPING.keys())}")
        return CMC_MAPPING.get(key, None)
    except Exception as e:
        logger.error(f"failed to get crypto mapping: {e}")
        return None
