import logging
from uuid import UUID

from app.services.contact_scouting import scout_contacts

logger = logging.getLogger(__name__)


async def run_scout_contacts(ctx: dict, brand_target_id: str, agency_id: str) -> dict:
    """ARQ job: scout contacts for a brand target via Apollo."""
    logger.info(f"Starting contact scouting job for brand target {brand_target_id}")
    await scout_contacts(UUID(brand_target_id), UUID(agency_id))
    return {"status": "completed", "brand_target_id": brand_target_id}
