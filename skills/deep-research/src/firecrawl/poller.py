import time
from typing import Optional

from ..models import PollResponse
from .client import FirecrawlClient


POLL_INTERVAL = 2.0


def poll_agent(
    job_id: str,
    *,
    client: Optional[FirecrawlClient] = None,
    interval: float = POLL_INTERVAL,
) -> PollResponse:
    """Poll GET /agent/{jobId} every `interval` seconds until the job is terminal."""
    c = client or FirecrawlClient()
    while True:
        data = c.get(f"/agent/{job_id}")
        result = PollResponse(**data)
        if result.status in ("completed", "failed"):
            return result
        time.sleep(interval)
