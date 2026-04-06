import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
MAX_RETRIES = 3
INITIAL_BACKOFF = 2.0


class ApolloClient:
    """Async Apollo API client with retry and backoff on 429s."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.apollo_api_key
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "x-api-key": self.api_key,
        }

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make a request with exponential backoff on rate limits."""
        url = f"{APOLLO_BASE_URL}{path}"
        kwargs.setdefault("headers", self.headers)

        backoff = INITIAL_BACKOFF
        for attempt in range(MAX_RETRIES + 1):
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(method, url, **kwargs)

            if response.status_code == 429:
                if attempt < MAX_RETRIES:
                    logger.warning(f"Apollo rate limited, retrying in {backoff}s (attempt {attempt + 1})")
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                logger.error("Apollo rate limit exceeded after all retries")
                response.raise_for_status()

            response.raise_for_status()
            return response.json()

        return {}

    async def enrich_organization(self, domain: str) -> dict | None:
        """
        Enrich an organization by domain.
        Returns org data including apollo organization_id, or None if not found.
        """
        try:
            data = await self._request(
                "GET",
                "/organizations/enrich",
                params={"domain": domain},
            )
            org = data.get("organization")
            if not org:
                logger.info(f"No Apollo org found for domain: {domain}")
                return None
            return org
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"No Apollo org found for domain: {domain}")
                return None
            raise

    async def search_people(
        self,
        organization_ids: list[str],
        person_titles: list[str],
        per_page: int = 10,
        include_similar_titles: bool = True,
    ) -> list[dict]:
        """
        Search for people at given organizations matching title keywords.
        Uses the api_search endpoint (free, returns obfuscated data with IDs).
        """
        payload = {
            "organization_ids": organization_ids,
            "person_titles": person_titles,
            "per_page": per_page,
            "page": 1,
            "include_similar_titles": include_similar_titles,
        }

        data = await self._request("POST", "/mixed_people/api_search", json=payload)
        return data.get("people", [])

    async def enrich_person(self, person_id: str) -> dict | None:
        """
        Enrich a person by their Apollo ID to get full name, email, title, etc.
        Returns the full person record, or None if not found.
        """
        try:
            data = await self._request("POST", "/people/match", json={"id": person_id})
            return data.get("person")
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (404, 422):
                logger.info(f"Could not enrich person {person_id}: {e.response.status_code}")
                return None
            raise


apollo_client = ApolloClient()
