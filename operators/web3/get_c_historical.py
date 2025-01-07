from typing import Optional

from pydantic import BaseModel

from echelon.common.config import SETTINGS
from echelon.operators.web3 import CmcOp


class GetCryptoHistoricalReq(BaseModel):
    id: Optional[str] = None
    convert: str = "USD"
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    interval: Optional[str] = "1h"
    count: int = 20


class GetCryptoHistorical(CmcOp):
    url: str = f"{SETTINGS.C_PRO_BASE_URL}/v2/cryptocurrency/quotes/historical"

    async def _to_resp(self, json: dict) -> Optional[dict]:
        return json
