from pydantic import BaseModel, Field, PrivateAttr
from typing import Optional
from datetime import datetime, timezone
from app.core.config import settings
from app.core.jwt_helper import JWTGenerator


class Tenant(BaseModel):
    tenant_id: str
    name: str
    snowflake_role: str
    snowflake_user: str = ""
    default_model: str = "claude-4-sonnet"
    allowed_models: list[str] = Field(default_factory=list)
    system_prompt: str = ""
    rate_limit_rpm: int = 60
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    _jwt_generator: Optional[JWTGenerator] = PrivateAttr(default=None)

    def set_jwt_generator(self, gen: JWTGenerator):
        self._jwt_generator = gen

    def get_auth_token(self) -> str:
        if self._jwt_generator is None:
            raise RuntimeError(f"No JWT generator for tenant {self.tenant_id}")
        return self._jwt_generator.get_token()


class APIKey(BaseModel):
    api_key: str
    tenant_id: str
    status: str = "active"


_alpha_jwt = JWTGenerator(
    account=settings.snowflake_account,
    user=settings.alpha_snowflake_user,
    private_key_path=settings.alpha_private_key_path,
)
_beta_jwt = JWTGenerator(
    account=settings.snowflake_account,
    user=settings.beta_snowflake_user,
    private_key_path=settings.beta_private_key_path,
)

_tenant_alpha = Tenant(
    tenant_id="tenant-alpha",
    name="User Alpha",
    snowflake_role="COCO_TENANT_ALPHA",
    snowflake_user=settings.alpha_snowflake_user,
    default_model="claude-4-sonnet",
    allowed_models=["claude-4-sonnet", "mistral-large2"],
    system_prompt="You are a helpful AI assistant for User Alpha.",
    rate_limit_rpm=60,
)
_tenant_alpha.set_jwt_generator(_alpha_jwt)

_tenant_beta = Tenant(
    tenant_id="tenant-beta",
    name="User Beta",
    snowflake_role="COCO_TENANT_BETA",
    snowflake_user=settings.beta_snowflake_user,
    default_model="openai-gpt-4.1",
    allowed_models=["openai-gpt-4.1", "llama3.1-70b", "deepseek-r1"],
    system_prompt="You are a helpful AI assistant for User Beta.",
    rate_limit_rpm=30,
)
_tenant_beta.set_jwt_generator(_beta_jwt)

TENANTS = {"tenant-alpha": _tenant_alpha, "tenant-beta": _tenant_beta}

API_KEYS = {
    "sk-alpha-secret-key-001": APIKey(api_key="sk-alpha-secret-key-001", tenant_id="tenant-alpha"),
    "sk-beta-secret-key-001": APIKey(api_key="sk-beta-secret-key-001", tenant_id="tenant-beta"),
}


def get_tenant_by_api_key(api_key: str) -> Tenant | None:
    key_record = API_KEYS.get(api_key)
    if not key_record or key_record.status != "active":
        return None
    return TENANTS.get(key_record.tenant_id)
