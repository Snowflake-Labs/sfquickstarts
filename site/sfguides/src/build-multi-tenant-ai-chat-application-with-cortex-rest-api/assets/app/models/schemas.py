from pydantic import BaseModel, Field, model_validator
from typing import Optional


class ChatRequest(BaseModel):
    message: Optional[str] = Field(
        default=None,
        description="Single user message. Use 'messages' for multi-turn.",
    )
    messages: Optional[list[dict]] = Field(
        default=None,
        description="Full conversation history as [{role, content}, ...].",
    )
    model: Optional[str] = Field(
        default=None,
        description="Which AI model to use. Uses tenant's default if omitted.",
    )
    max_tokens: int = Field(
        default=4096, ge=1, le=16384,
        description="Max length of the AI response (in tokens).",
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description="Creativity dial: 0.0 = focused, 1.0 = creative.",
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Optional tracking info (session_id, user_id, etc.).",
    )

    @model_validator(mode="after")
    def require_message_or_messages(self):
        if not self.message and not self.messages:
            raise ValueError("Either 'message' or 'messages' must be provided.")
        return self

    def get_messages(self, system_prompt: str = "") -> list[dict]:
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        if self.messages:
            msgs.extend(self.messages)
        else:
            msgs.append({"role": "user", "content": self.message})
        return msgs


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail
