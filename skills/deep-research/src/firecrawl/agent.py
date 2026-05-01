from typing import Any, Literal, Optional

from ..models import AgentRequest, AgentStartResponse
from .client import FirecrawlClient


def start_agent(
    prompt: str,
    *,
    client: Optional[FirecrawlClient] = None,
    urls: Optional[list[str]] = None,
    schema: Optional[dict[str, Any]] = None,
    max_credits: Optional[int] = None,
    strict_constrain_to_urls: Optional[bool] = None,
    model: Optional[Literal["spark-1-mini", "spark-1-pro"]] = None,
) -> str:
    """Start a Firecrawl agent job. Returns the job ID."""
    request = AgentRequest(
        prompt=prompt,
        urls=urls,
        schema_=schema,
        max_credits=max_credits,
        strict_constrain_to_urls=strict_constrain_to_urls,
        model=model,
    )
    body = request.model_dump(by_alias=True, exclude_none=True)
    c = client or FirecrawlClient()
    response = AgentStartResponse(**c.post("/agent", body))
    return response.id
