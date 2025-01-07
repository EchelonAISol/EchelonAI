from fastapi import APIRouter
from starlette.responses import StreamingResponse

from echelon.operators.llm.chat_op import ChatReq, ChatOp
from echelon.operators.llm.image_answer_op import ImageAnswerOp, ImageReq
from echelon.operators.llm.summariz_op import SummarizOp, SummaryResp, SummaryReq
from echelon.routers import RestResponse

chat_router = APIRouter()


@chat_router.post("/api/echelon/ai/summariz",
                  response_model=RestResponse[SummaryResp])
async def summariz(req: SummaryReq):
    """"""
    ret = await SummarizOp().predict(req)
    return RestResponse(data=ret)


@chat_router.get("/api/echelon/ai/chat")
async def chat(req: ChatReq):
    return StreamingResponse(ChatOp().stream(input=req), media_type="text/event-stream")


@chat_router.post("/api/echelon/ai/image/chat")
async def image_chat(req: ImageReq):
    return StreamingResponse(ImageAnswerOp().stream(input=req), media_type="text/event-stream")
