import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router as v1_router
from app.services.cortex_client import cortex_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await cortex_client.close()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app = FastAPI(
    title="CoCo Cortex AI Gateway",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(v1_router, prefix="/v1")


@app.get("/healthz")
async def health_check():
    return {"status": "ok"}
