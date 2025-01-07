from typing import Optional, List

from pydantic import BaseModel, Field, field_validator
from pyecharts.charts import Tree
from pyecharts.charts.base import Base

from echelon.operators.llm import EChartOp, EChartOpReq

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


class TreeMindMapEchartOp(EChartOp):
    default_human_prompt: str = DEFAULT_HUMAN_PROMPT
    llm_output_model: type[BaseModel] | str = TreeMindmap

    async def _to_chart(self, input: EChartOpReq, llm_output: Optional[TreeMindmap]) -> Optional[Base]:
        if not isinstance(llm_output, TreeMindmap):
            return None

        tree = (
            Tree()
            .add("", data=[llm_output.model_dump(exclude_none=True)], )
        )
        return tree
