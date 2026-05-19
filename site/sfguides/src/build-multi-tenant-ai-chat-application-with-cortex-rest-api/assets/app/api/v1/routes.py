import logging
from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse
from app.models.schemas import ChatRequest, ErrorResponse
from app.core.tenants import Tenant
from app.api.v1.dependencies import require_tenant
from app.services.cortex_client import cortex_client

logger = logging.getLogger("coco.routes")
router = APIRouter()


@router.post(
    "/chat/stream",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Chat with an AI model via Cortex (streaming SSE)",
)
async def chat_stream(
    request: ChatRequest,
    tenant: Tenant = Depends(require_tenant),
):
    generator = cortex_client.chat_complete_stream(
        request=request,
        tenant_id=tenant.tenant_id,
        default_model=tenant.default_model,
        auth_token=tenant.get_auth_token(),
        system_prompt=tenant.system_prompt,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
