from typing import Optional, List, AsyncIterator

from pydantic import BaseModel, Field, field_validator

from echelon.operators.llm import EChartOpReq, LLMPredictOp

DEFAULT_HUMAN_PROMPT = """\
You are a helpful assistant. Your task is to extract structured data from the text needed to create a tree-shaped mind map.

## Requirements
- The output should be in English.

The text is as follows:

{text}\
"""


class TreeMindmap(BaseModel):
    """Tree-shaped mind map"""
    name: str = Field(default="", description="Node Description")
    children: Optional[List["TreeMindmap"]] = Field(default=None, description="Child nodes, same type as TreeMindmap")

    @field_validator('children', mode='before')
    def validator_children(cls, v):
        if isinstance(v, list):
            if not v:
                return None
            return v
        return None

    def to_markdown(self, level=-1) -> str:
        """Convert TreeMindmap to markdown unordered list"""
        markdown = ""
        if level < 0:
            if self.children:
                for child in self.children:
                    markdown += child.to_markdown(level + 1)
        indent = "  " * level
        markdown = f"{indent}- {self.name}\n"
        if self.children:
            for child in self.children:
                markdown += child.to_markdown(level + 1)
        return markdown


class GoogleMindMapOp(LLMPredictOp):
    default_human_prompt: str = DEFAULT_HUMAN_PROMPT
    llm_output_model: type[BaseModel] | str = TreeMindmap

    async def predict(self, req: EChartOpReq) -> TreeMindmap:
        return await self._predict_default(req)

    async def stream(self, input: EChartOpReq) -> AsyncIterator:
        raise NotImplementedError
