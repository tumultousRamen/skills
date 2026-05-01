from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    prompt: str = Field(..., max_length=10000)
    urls: Optional[list[str]] = None
    schema_: Optional[dict[str, Any]] = Field(None, serialization_alias="schema")
    max_credits: Optional[int] = Field(None, serialization_alias="maxCredits")
    strict_constrain_to_urls: Optional[bool] = Field(None, serialization_alias="strictConstrainToURLs")
    model: Optional[Literal["spark-1-mini", "spark-1-pro"]] = None

    model_config = {"populate_by_name": True}


class AgentStartResponse(BaseModel):
    success: bool
    id: str


class PollResponse(BaseModel):
    success: bool
    status: Literal["processing", "completed", "failed"]
    data: Optional[Any] = None
    model: Optional[str] = None
    error: Optional[str] = None
    expires_at: Optional[str] = Field(None, alias="expiresAt")
    credits_used: Optional[int] = Field(None, alias="creditsUsed")

    model_config = {"populate_by_name": True}


class CancelResponse(BaseModel):
    success: bool
