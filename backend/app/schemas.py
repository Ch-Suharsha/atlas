from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str = Field(..., min_length=1, max_length=128)
    session_token: Optional[str] = Field(default=None, min_length=16, max_length=128)
    # Kept as deprecated response-compatible fields for older clients. The API
    # deliberately does not use either value as proof of identity.
    customer_id: Optional[str] = Field(default=None, deprecated=True)
    customer_email: Optional[str] = Field(default=None, deprecated=True)


class ToolInvocation(BaseModel):
    name: str
    arguments: dict
    result: dict


class RagSource(BaseModel):
    asin: str
    title: str
    score: float
    category: Optional[str] = None
    price: Optional[float] = None


class ChatResponse(BaseModel):
    reply: str
    sentiment: str
    intent: str
    escalated: bool = False
    customer_verified: bool = False
    tools_called: List[ToolInvocation] = []
    rag_sources: List[RagSource] = []
    session_id: str
    session_token: str


class HealthResponse(BaseModel):
    status: str
    checks: dict[str, Any]
