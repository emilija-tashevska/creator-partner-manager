import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.creator import Creator
from app.schemas.enrichment import CreatorEnrichmentOutput
from app.services.llm import generate_structured

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "creator_enrichment.txt"
PROMPT_TEMPLATE = PROMPT_PATH.read_text()

SYSTEM_INSTRUCTION = (
    "You are an expert social media and influencer marketing analyst. "
    "You produce structured creator profiles from minimal input data. "
    "Be accurate, professional, and honest about confidence levels."
)


async def enrich_creator(creator_id: UUID, agency_id: UUID) -> None:
    """Run LLM enrichment for a creator and save the results to the database."""
    async with async_session() as db:
        creator = await _load_creator(db, creator_id, agency_id)
        if not creator:
            logger.error(f"Creator {creator_id} not found for enrichment")
            return

        creator.enrichment_status = "processing"
        await db.commit()

        try:
            result = await _call_llm(creator)
            await _save_result(db, creator, result)
            logger.info(f"Enrichment completed for creator {creator_id}")
        except Exception as e:
            logger.error(f"Enrichment failed for creator {creator_id}: {e}")
            creator.enrichment_status = "failed"
            await db.commit()
            raise


async def _load_creator(
    db: AsyncSession, creator_id: UUID, agency_id: UUID
) -> Creator | None:
    result = await db.execute(
        select(Creator).where(Creator.id == creator_id, Creator.agency_id == agency_id)
    )
    return result.scalar_one_or_none()


async def _call_llm(creator: Creator) -> CreatorEnrichmentOutput:
    prompt = PROMPT_TEMPLATE.format(
        name=creator.name,
        instagram_handle=creator.instagram_handle or "N/A",
        tiktok_handle=creator.tiktok_handle or "N/A",
        youtube_handle=creator.youtube_handle or "N/A",
        x_handle=creator.x_handle or "N/A",
        content_links=", ".join(creator.content_links or []) or "None provided",
        niche=creator.niche or "Not specified",
        audience_size_approx=creator.audience_size_approx or "Unknown",
    )

    return await generate_structured(
        prompt=prompt,
        output_schema=CreatorEnrichmentOutput,
        system_instruction=SYSTEM_INSTRUCTION,
    )


async def _save_result(
    db: AsyncSession, creator: Creator, result: CreatorEnrichmentOutput
) -> None:
    creator.bio_summary = result.bio_summary
    creator.content_style = result.content_style
    creator.audience_demographics = result.audience_demographics.model_dump()
    creator.tone_descriptors = result.tone_descriptors
    creator.collaboration_types = result.collaboration_types
    creator.collaboration_verticals = result.collaboration_verticals
    creator.enrichment_status = "completed"
    await db.commit()
