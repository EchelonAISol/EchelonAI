from typing import List, AsyncIterator, Optional

from langchain_core.documents import Document
from pydantic import BaseModel, computed_field, Field

from echelon.operators.llm import LLMPredictOp, BaseModelInput
from echelon.operators.llm.search_answer_op import SearchAnswerReq

DEFAULT_HUMAN_PROMPT = """\
You are a helpful assistant. Your task is to propose relevant questions based on the user’s original question and the context.

## Requirements
- Make full use of the context information
- Generate 3 relevant questions
- Each relevant question should not exceed 20 words
- The output should be in English.

## Below is a set of context

{context}

## Below is the user’s original question

{user_input}\
"""


class Questions(BaseModel):
    """
    Questions
    """
    questions: List[str] = Field(default_factory=list, description="Related Questions List")


class RelatedQuestionsReq(BaseModel):
    user_input: str
    resources: Optional[List[Document]] = None

    @computed_field
    @property
    def context(self) -> str:
        if not self.resources:
            return "No relevant context, please use your own"

        context = ""
        for doc in self.resources:
            if doc.page_content:
                context += f"{doc.page_content}"
                if doc.metadata.get('created_at'):
                    context += f"created_at \n{doc.metadata.get('created_at')}"
                context += "\n\n"
        return context


class RelatedQuestionsOp(LLMPredictOp):
    llm_output_model: type[BaseModel] | str = Questions
    default_human_prompt: str = DEFAULT_HUMAN_PROMPT

    async def predict(self, req: SearchAnswerReq) -> Questions:
        return await self._predict_default(req)

    async def stream(self, input: BaseModelInput) -> AsyncIterator:
        raise NotImplementedError
