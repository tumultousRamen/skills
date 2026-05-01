from typing import Optional

from ..models import CancelResponse
from .client import FirecrawlClient


def cancel_agent(
    job_id: str,
    *,
    client: Optional[FirecrawlClient] = None,
) -> bool:
    """Cancel an in-progress agent job. Returns True if cancellation succeeded."""
    c = client or FirecrawlClient()
    data = c.delete(f"/agent/{job_id}")
    return CancelResponse(**data).success
