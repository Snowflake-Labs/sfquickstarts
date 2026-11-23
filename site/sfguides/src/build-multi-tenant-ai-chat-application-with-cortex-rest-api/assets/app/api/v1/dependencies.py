import time
from collections import defaultdict
from fastapi import Header, HTTPException
from app.core.tenants import Tenant, get_tenant_by_api_key

_rate_limit_buckets: dict[str, list[float]] = defaultdict(list)


async def require_tenant(
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> Tenant:
    tenant = get_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail={
            "code": "UNAUTHORIZED",
            "message": "Invalid or missing API key. Check your X-API-Key header.",
        })

    now = time.time()
    bucket = _rate_limit_buckets[tenant.tenant_id]
    _rate_limit_buckets[tenant.tenant_id] = [t for t in bucket if now - t < 60.0]
    if len(_rate_limit_buckets[tenant.tenant_id]) >= tenant.rate_limit_rpm:
        raise HTTPException(status_code=429, detail={
            "code": "RATE_LIMITED",
            "message": f"Rate limit exceeded ({tenant.rate_limit_rpm} req/min).",
        })
    _rate_limit_buckets[tenant.tenant_id].append(now)

    return tenant
