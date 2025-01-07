from typing import List, Any, AsyncIterator, Optional

from langchain_core.documents import Document
from pydantic import BaseModel, computed_field

from echelon.operators.llm import LLMPredictOp

DEFAULT_HUMAN_PROMPT = """\
You are a helpful AI analyze assistant. Your task is to analyze the question based on the context.

## Steps
1. Analyze the tweets in context one by one, and summarize their key point if the tweets are related to the question
2. Filter out irrelevant key point
3. Merge and sort all key point, key point held by more users are ranked first, and it is necessary to keep which users have the same key point.
4. Summarize the conclusions of your analysis

## Requirements
- Do not make up users’ key point
- All key point can be said to come from a user or yourself, but not from the context
- The output should be markdown
- The output should be in English

<Output format>

## Summary

... ...

## Key Points

- Point 1: ... ...

- Point 2: .. ...

... ...

</Output format>

## Below is a set of context

{context}

## Below is the question

{user_input}\
"""

DEFAULT_HUMAN_PROMPT_1 = """\
You are a helpful AI search assistant. Your task is to answer the questions asked by users based on the context.

## Requirements
- Make full use of context information, but don't blindly repeat the context verbatim
- The answer must be concise, correct and accurate
- The output should be in English.

## Below is a set of context

{context}

## Below is the user’s question

{user_input}\
"""


class SearchAnswerReq(BaseModel):
    user_input: str
    resources: Optional[List[Document]] = None

    @computed_field
    @property
    def context(self) -> str:
        if not self.resources:
            return "No relevant context was found. Please use your knowledge to answer the question."

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


class SearchAnswerOp(LLMPredictOp):
    default_human_prompt: str = DEFAULT_HUMAN_PROMPT

    async def predict(self, input: SearchAnswerReq) -> Any:
        raise NotImplementedError()

    async def stream(self, input: SearchAnswerReq) -> AsyncIterator:
        async for chunk in self._stream_default(input):
            yield chunk
