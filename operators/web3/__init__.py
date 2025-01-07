import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Optional, Any

import aiohttp
from pydantic import BaseModel

from echelon.common.config import SETTINGS

BaseModelInput = TypeVar("BaseModelInput", bound=BaseModel, contravariant=True)

logger = logging.getLogger(__name__)


class CmcOp(ABC, BaseModel):
    url: str

    async def call(self, input: BaseModelInput = None) -> Optional[Any]:
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': SETTINGS.C_PRO_API_KEY,
        }

        params = await self._to_params(input)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, headers=headers, params=params) as response:
                    response.raise_for_status()
                    json = await response.json()
                    return await self._to_resp(json)
        except Exception as e:
            logging.error(e)

        return None

    async def _to_params(self, input: BaseModelInput) -> Optional[Any]:
        if input:
            return input.model_dump(exclude_none=True)
        return None

    @abstractmethod
    async def _to_resp(self, json: dict) -> Optional[Any]:
        raise NotImplementedError()
