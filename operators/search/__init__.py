import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Optional, List

from langchain_core.documents import Document
from pydantic import BaseModel

from echelon.common.config import SETTINGS

logger = logging.getLogger(__name__)

BaseModelInput = TypeVar("BaseModelInput", bound=BaseModel, contravariant=True)


class SearchOp(ABC):

    @abstractmethod
    async def search(self, input: BaseModelInput) -> Optional[List[Document]]:
        raise NotImplementedError


banned_tokens = set()


def print_token_with_masking(token: str):
    if len(token) > 8:
        masked_token = token[:4] + '*' * (len(token) - 8) + token[-4:]
        logger.info(masked_token)


def token_generator(tokens):
    while True:
        for token in tokens:
            yield token


token_gen = token_generator(SETTINGS.X_BEARER_TOKENS)


def get_x_token(num: int = 0) -> str:
    cur_token = next(token_gen)

    if cur_token:
        if cur_token in banned_tokens:
            if num > 0:
                print_token_with_masking(cur_token)
                return cur_token
            logger.warning(f"Token {cur_token} is banned and will be skipped.")
            return get_x_token(1)

    print_token_with_masking(cur_token)
    return cur_token


def ban_token(token: str):
    banned_tokens.add(token)
    logger.warning(f"Token {token} has been banned.")
