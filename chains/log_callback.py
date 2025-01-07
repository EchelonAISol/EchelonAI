import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

from echelon.common.codec import jsondumps

logger = logging.getLogger(__name__)


class LLMLogCallbackHandler(AsyncCallbackHandler):

    async def on_llm_start(
            self,
            serialized: Dict[str, Any],
            prompts: List[str],
            *,
            run_id: UUID,
            parent_run_id: Optional[UUID] = None,
            tags: Optional[List[str]] = None,
            metadata: Optional[Dict[str, Any]] = None,
            **kwargs: Any,
    ) -> Any:
        logger.info(f"on_llm_start prompt: {prompts} args: {kwargs}")

    async def on_llm_end(
            self,
            response: LLMResult,
            *,
            run_id: UUID,
            parent_run_id: Optional[UUID] = None,
            **kwargs: Any,
    ) -> Any:
        response_json = jsondumps(response.model_dump())
        logger.info(f"on_llm_end {response_json}")
