import logging
from uuid import UUID

from app.services.enrichment import enrich_creator

logger = logging.getLogger(__name__)


async def run_enrichment(ctx: dict, creator_id: str, agency_id: str) -> dict:
    """ARQ job: enrich a creator profile via LLM."""
    logger.info(f"Starting enrichment job for creator {creator_id}")
    await enrich_creator(UUID(creator_id), UUID(agency_id))
    return {"status": "completed", "creator_id": creator_id}
