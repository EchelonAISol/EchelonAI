import logging

from fastapi import APIRouter, Request, Query
from sse_starlette import EventSourceResponse

from echelon.agent.ai_search_agent import AISearchAgent

logger = logging.getLogger(__name__)

ai_search_router = APIRouter()


@ai_search_router.get("/api/echelon/ai/search")
async def ai_search(query: str = Query(...)):
    return EventSourceResponse(AISearchAgent().search(query))


@ai_search_router.get("/api/echelon/oauth/callback")
async def callback(request: Request):
    logger.info(f"Received callback: {request.url or ''} params: {request.query_params}")
    return {"message": "OAuth callback successful", "token_response": "echelon_token_response"}
