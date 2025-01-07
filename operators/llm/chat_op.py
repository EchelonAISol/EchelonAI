from typing import Any, AsyncIterator

from pydantic import BaseModel

from echelon.operators.llm import LLMPredictOp

DEFAULT_HUMAN_PROMPT = "{user_input}"


class ChatReq(BaseModel):
    user_input: str


class ChatOp(LLMPredictOp):
    default_human_prompt: str = DEFAULT_HUMAN_PROMPT

    async def predict(self, input: ChatReq) -> Any:
        raise NotImplementedError()

    async def stream(self, input: ChatReq) -> AsyncIterator:
        async for chunk in self._stream_default(input):
            yield chunk
