from typing import List, AsyncIterator

from pydantic import Field, BaseModel

from echelon.operators.llm import LLMPredictOp, UserInputReq, BaseModelInput

DEFAULT_HUMAN_PROMPT = """\
Your task is to rewrite the user input into [1, 3] queries suitable for search engines to help users analyze relevant virtual currency market conditions.

## Requirements
- The output should be in English.

user input: {user_input}

Queries:\
"""


class Queries(BaseModel):
    """
    Queries
    """
    queries: List[str] = Field(default_factory=list, description="search engine queries")


class QueryRewritingOp(LLMPredictOp):
    llm_output_model: type[BaseModel] | str = Queries
    default_human_prompt: str = DEFAULT_HUMAN_PROMPT

    async def predict(self, req: UserInputReq) -> Queries:
        return await self._predict_default(req)

    async def stream(self, input: BaseModelInput) -> AsyncIterator:
        raise NotImplementedError
