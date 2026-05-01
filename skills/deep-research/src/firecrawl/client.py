import os
from typing import Any

import requests


BASE_URL = "https://api.firecrawl.dev/v2"


class FirecrawlClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FIRECRAWL_API_KEY is not set. "
                "Add it to ~/.claude/settings.json under the 'env' key:\n"
                '  { "env": { "FIRECRAWL_API_KEY": "fc-..." } }'
            )
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        resp = self._session.post(f"{BASE_URL}{path}", json=body)
        self._raise(resp)
        return resp.json()

    def get(self, path: str) -> dict[str, Any]:
        resp = self._session.get(f"{BASE_URL}{path}")
        self._raise(resp)
        return resp.json()

    def delete(self, path: str) -> dict[str, Any]:
        resp = self._session.delete(f"{BASE_URL}{path}")
        self._raise(resp)
        return resp.json()

    @staticmethod
    def _raise(resp: requests.Response) -> None:
        if resp.status_code == 402:
            raise RuntimeError("Firecrawl: payment required — check your credit balance.")
        if resp.status_code == 429:
            raise RuntimeError("Firecrawl: rate limit exceeded — slow down and retry.")
        resp.raise_for_status()
