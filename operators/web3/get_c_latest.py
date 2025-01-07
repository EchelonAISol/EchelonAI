from typing import Optional

from pydantic import BaseModel

from echelon.common.config import SETTINGS
from echelon.operators.web3 import CmcOp


class GetCryptoLatestReq(BaseModel):
    id: Optional[int] = None
    convert: str = "USD"


class GetCryptoLatest(CmcOp):
    url: str = f"{SETTINGS.C_PRO_BASE_URL}/v2/cryptocurrency/quotes/latest"

    async def _to_resp(self, json: dict) -> Optional[dict]:
        return json
