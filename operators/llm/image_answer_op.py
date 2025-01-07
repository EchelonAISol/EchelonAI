from typing import AsyncIterator, Any, Optional

from pydantic import BaseModel

from echelon.operators.llm import LLMPredictOp

DEFAULT_HUMAN_PROMPT = """\
You are an expert in image content analysis and summarization, skilled in providing detailed descriptions and extracting key information from various types of visual data. Please generate a detailed description and in-depth explanation of the key information from the input image according to the following requirements:

## Requirements
1. General Requirements:  
- The description must be as detailed and objective as possible, including both summary and key points, and formatted in Markdown. The response should be more than 300 words.  
- Avoid any subjective assumptions and only describe the visible objective information in the image, such as text, graphics, numbers, colors, arrows, legends, box structures, etc.  
- The response must be in English.  
- Provide in-depth explanations of key areas, key technologies, key logical relationships, or key components.  
- Summarize and explain the function of core elements, their relevance, and their relationship to the overall context based on the image’s theme.  
- If there is any data in the image, you may perform data analysis.

2. For statistical charts:  
- Extract all data from the chart, including numbers, proportions, trends, axis information, and legends.  
- Perform a basic analysis of the data, such as trend changes, peaks, lowest values, and distribution characteristics.

3. For flowcharts:  
- Clearly describe the content, name, and shape of each node.  
- Describe all arrows and connections, their directions, logical sequence, and the relationships and hierarchy between nodes.  
- When describing the flow, ensure that the flow has not already been described; avoid repeating steps or sections.

4. For architecture diagrams:  
- List all components, modules, and hierarchical structures in the architecture diagram.  
- Describe the relationships between components (including both horizontal connections and vertical hierarchies without missing any relations).  
- If there are vertical or horizontal layers, clearly explain the upstream and downstream relationships or lateral dependencies.

5. For other types of images:  
- Accurately describe all visible elements in the image, such as shapes, text, identifiers, numbers, color schemes, and layout.  
- Extract all textual information fully; if there are numbers, markers, or symbols, list them one by one.  
- If there are lines, arrows, directional indicators, or relationships between elements, provide a detailed explanation.

## Image Context

Below are some words near the image to help you understand the image

Context: {text}

## Begin Response: Provide as much detail as possible (more than 300 words); please check and avoid infinite loops\
"""


class ImageReq(BaseModel):
    """
    Queries
    """
    image_url: str
    text: Optional[str] = ""


class ImageAnswerOp(LLMPredictOp):
    default_human_prompt: str = DEFAULT_HUMAN_PROMPT

    async def predict(self, input: ImageReq) -> Any:
        raise NotImplementedError()

    async def stream(self, input: ImageReq) -> AsyncIterator:
        async for chunk in self._stream_default(input):
            yield chunk
