import json
import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.brand_target import BrandTarget
from app.models.creator import Creator
from app.schemas.brand import BrandDiscoveryOutput
from app.services.llm import generate_structured, FAST_MODEL

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "brand_discovery.txt"
PROMPT_TEMPLATE = PROMPT_PATH.read_text()

SYSTEM_INSTRUCTION = (
    "You are an expert brand partnerships strategist who identifies ideal "
    "sponsor-creator matches. You only suggest real, existing companies. "
    "You provide actionable reasoning for every suggestion."
)


async def discover_brands(creator_id: UUID, agency_id: UUID) -> None:
    """Run LLM brand discovery for a creator and persist suggestions."""
    async with async_session() as db:
        creator = await _load_creator(db, creator_id, agency_id)
        if not creator:
            logger.error(f"Creator {creator_id} not found for brand discovery")
            return

        if creator.enrichment_status != "completed":
            logger.error(f"Creator {creator_id} not yet enriched, skipping brand discovery")
            return

        discovery_round = await _next_discovery_round(db, creator_id)

        try:
            exclusion_list = await _get_exclusion_list(db, creator_id)
            result = await _call_llm(creator, exclusion_list)
            await _save_suggestions(db, creator, result, discovery_round)
            logger.info(
                f"Brand discovery round {discovery_round} completed for creator {creator_id}: "
                f"{len(result.suggestions)} suggestions"
            )
        except Exception as e:
            logger.error(f"Brand discovery failed for creator {creator_id}: {e}")
            raise


async def _load_creator(
    db: AsyncSession, creator_id: UUID, agency_id: UUID
) -> Creator | None:
    result = await db.execute(
        select(Creator).where(Creator.id == creator_id, Creator.agency_id == agency_id)
    )
    return result.scalar_one_or_none()


async def _next_discovery_round(db: AsyncSession, creator_id: UUID) -> int:
    result = await db.execute(
        select(sa_func.coalesce(sa_func.max(BrandTarget.discovery_round), 0)).where(
            BrandTarget.creator_id == creator_id
        )
    )
    return result.scalar_one() + 1


async def _get_exclusion_list(db: AsyncSession, creator_id: UUID) -> list[str]:
    """Get company names/domains already suggested, approved, or blacklisted for this creator."""
    result = await db.execute(
        select(BrandTarget.company_name, BrandTarget.company_domain).where(
            BrandTarget.creator_id == creator_id
        )
    )
    exclusions = []
    for name, domain in result.all():
        exclusions.append(name)
        if domain:
            exclusions.append(domain)
    return exclusions


def _format_exclusion_section(exclusion_list: list[str]) -> str:
    if not exclusion_list:
        return "No brands to exclude — this is the first discovery round."
    joined = ", ".join(exclusion_list)
    return (
        f"IMPORTANT — Exclude these brands (already suggested or acted upon):\n"
        f"{joined}\n\n"
        f"Do NOT suggest any brand from the above list or their obvious subsidiaries."
    )


async def _call_llm(creator: Creator, exclusion_list: list[str]) -> BrandDiscoveryOutput:
    demographics_str = json.dumps(creator.audience_demographics) if creator.audience_demographics else "Not available"

    prompt = PROMPT_TEMPLATE.format(
        creator_name=creator.name,
        bio_summary=creator.bio_summary or "Not available",
        content_style=creator.content_style or "Not available",
        audience_demographics=demographics_str,
        collaboration_types=", ".join(creator.collaboration_types or []) or "Not specified",
        collaboration_verticals=", ".join(creator.collaboration_verticals or []) or "Not specified",
        audience_size_approx=creator.audience_size_approx or "Unknown",
        exclusion_section=_format_exclusion_section(exclusion_list),
    )

    return await generate_structured(
        prompt=prompt,
        output_schema=BrandDiscoveryOutput,
        model=FAST_MODEL,
        system_instruction=SYSTEM_INSTRUCTION,
    )


async def _save_suggestions(
    db: AsyncSession,
    creator: Creator,
    result: BrandDiscoveryOutput,
    discovery_round: int,
) -> None:
    for suggestion in result.suggestions:
        brand = BrandTarget(
            agency_id=creator.agency_id,
            creator_id=creator.id,
            company_name=suggestion.company_name,
            company_domain=suggestion.company_domain,
            reasoning=suggestion.reasoning,
            status="suggested",
            discovery_round=discovery_round,
        )
        db.add(brand)
    await db.commit()
