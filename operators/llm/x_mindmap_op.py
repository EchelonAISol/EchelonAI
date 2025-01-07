from typing import List, AsyncIterator, Optional

from langchain_core.documents import Document
from pydantic import BaseModel, Field, computed_field

from echelon.operators.llm import LLMPredictOp, BaseModelInput

DEFAULT_HUMAN_PROMPT = """\
You are a helpful assistant. Your task is to summarize and extract the Twitter username all the tweets one by one.

## Requirements
- The output should be in English.

## Below is a set of Twitter Content

{context}\
"""


class XmindMapReq(BaseModel):
    resources: Optional[List[Document]] = None

    @computed_field
    @property
    def context(self) -> str:
        if not self.resources:
            return "No relevant context was found. Please use your knowledge to answer the user's question."

        context = ""
        for doc in self.resources:
            if doc.page_content:
                context += f"{doc.page_content}\n"
                if doc.metadata.get('created_at'):
                    context += f"created_at \n{doc.metadata.get('created_at')}"
                if doc.metadata.get('username'):
                    context += f"username \n{doc.metadata.get('username')}"
                context += "\n\n"
        return context


class TwitterSummary(BaseModel):
    twitter_user_name: str = Field(..., description="User's twitter username")
    content_summary: str = Field(..., description="The summary of the twitter content.")


class TwitterSummaryResp(BaseModel):
    summaries: List[TwitterSummary] = Field(..., description="List of Twitter summaries")


class XmindMapOp(LLMPredictOp):
    llm_output_model: type[BaseModel] | str = TwitterSummaryResp
    default_human_prompt: str = DEFAULT_HUMAN_PROMPT

    async def predict(self, req: XmindMapReq) -> TwitterSummaryResp:
        return await self._predict_default(req)

    async def stream(self, input: BaseModelInput) -> AsyncIterator:
        raise NotImplementedError
