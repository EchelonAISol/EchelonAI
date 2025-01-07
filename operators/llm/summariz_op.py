from typing import List, Optional

from pydantic import BaseModel, Field

from echelon.operators.llm import LLMPredictOp

DEFAULT_HUMAN_PROMPT = """\
You are a helpful assistant. Please summarize the webpage content provided by the user.

## Requirements:
- The summarized content must be as detailed and objective as possible
- The output should be in English
- Provide in-depth explanations for key areas, key technologies, and key logical relationships
- If there is any data information, perform data analysis
- To summarize everyone's posts on the webpage content
- replylist refers to all replies, including for each reply: username and reply.
- replypoints is an array of key words representing opinions or dislikes extracted from the replylist, not full sentences, e.g., ["good", "bad", "ugly"].
- The summary should be as detailed as possible, with near 200 words.

The webpage content is as follows:

{content}\
"""


class Summarize(BaseModel):
    """
    Summarize
    """
    summary: str = Field(..., description="Summary")
    key_points: List[str] = Field(..., description="KeyPoints")


class Reply(BaseModel):
    username: str = Field(..., description="Username")
    reply: str = Field(..., description="Reply")


class Post(BaseModel):
    """
    Post
    """
    username: str = Field(..., description="Username")
    summarize: Summarize = Field(..., description="Summarize")
    posttime: str = Field(..., description="Posttime. YYYY-MM-DD")
    replylist: Optional[List[str]] = Field(default_factory=list, description="Replylist")
    replypoints: Optional[List[str]] = Field(default_factory=list, description="Replypoints")


class SummaryResp(BaseModel):
    """
    Post Summary Resp
    """
    summaries: List[Post] = Field(default_factory=list, description="Summaries List")


class SummaryReq(BaseModel):
    content: str


class SummarizOp(LLMPredictOp):
    llm_output_model: type[BaseModel] | str = SummaryResp
    default_human_prompt: str = DEFAULT_HUMAN_PROMPT

    async def predict(self, req: SummaryReq) -> SummaryResp:
        return await self._predict_default(req)

    async def stream(self, input: SummaryReq) -> SummaryResp:
        raise NotImplementedError
