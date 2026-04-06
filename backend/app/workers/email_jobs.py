import logging
from uuid import UUID

from app.services.email_drafter import draft_emails

logger = logging.getLogger(__name__)


async def run_draft_emails(
    ctx: dict,
    contact_ids: list[str],
    creator_id: str,
    brand_target_id: str,
    agency_id: str,
    user_id: str,
) -> dict:
    """ARQ job: draft outreach emails for selected contacts via LLM."""
    logger.info(
        f"Starting email drafting job for {len(contact_ids)} contacts, "
        f"creator {creator_id}, brand {brand_target_id}"
    )
    await draft_emails(
        contact_ids=[UUID(cid) for cid in contact_ids],
        creator_id=UUID(creator_id),
        brand_target_id=UUID(brand_target_id),
        agency_id=UUID(agency_id),
        user_id=UUID(user_id),
    )
    return {"status": "completed", "contacts_count": len(contact_ids)}
