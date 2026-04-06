import logging
from uuid import UUID

from app.services.brand_discovery import discover_brands

logger = logging.getLogger(__name__)


async def run_brand_discovery(ctx: dict, creator_id: str, agency_id: str) -> dict:
    """ARQ job: discover brand targets for a creator via LLM."""
    logger.info(f"Starting brand discovery job for creator {creator_id}")
    await discover_brands(UUID(creator_id), UUID(agency_id))
    return {"status": "completed", "creator_id": creator_id}
