from fastapi import APIRouter

probe_router = APIRouter()


@probe_router.get("/healthz/liveness")
async def liveness():
    return "UP"


@probe_router.get("/healthz/readiness")
async def readiness():
    return "UP"
