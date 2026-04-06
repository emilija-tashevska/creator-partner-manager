import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.brand_target import BrandTarget
from app.models.contact import Contact
from app.models.creator import Creator
from app.models.outreach_email import OutreachEmail
from app.schemas.email import EmailDraftOutput
from app.services.llm import generate_structured, QUALITY_MODEL

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "email_draft.txt"
PROMPT_TEMPLATE = PROMPT_PATH.read_text()

SYSTEM_INSTRUCTION = (
    "You are a professional outreach copywriter for influencer-brand partnerships. "
    "You write concise, personalized emails that are warm but professional. "
    "Never fabricate metrics. Never use exclamation marks in subject lines."
)


async def draft_emails(
    contact_ids: list[UUID],
    creator_id: UUID,
    brand_target_id: UUID,
    agency_id: UUID,
    user_id: UUID,
) -> None:
    """Draft outreach emails for each contact via LLM."""
    async with async_session() as db:
        creator = await _load_creator(db, creator_id, agency_id)
        if not creator:
            logger.error(f"Creator {creator_id} not found for email drafting")
            return

        brand = await _load_brand_target(db, brand_target_id, agency_id)
        if not brand:
            logger.error(f"BrandTarget {brand_target_id} not found for email drafting")
            return

        contacts = await _load_contacts(db, contact_ids, agency_id)
        if not contacts:
            logger.error("No valid contacts found for email drafting")
            return

        has_media_kit = bool(creator.media_kit_file_path or creator.media_kit_url)

        for contact in contacts:
            try:
                result = await _call_llm(creator, brand, contact, has_media_kit)
                await _save_email(
                    db, agency_id, user_id, creator, brand, contact, result, has_media_kit
                )
                logger.info(f"Drafted email for {contact.email} at {brand.company_name}")
            except Exception as e:
                logger.error(
                    f"Failed to draft email for {contact.email}: {e}"
                )

        await db.commit()


async def _load_creator(
    db: AsyncSession, creator_id: UUID, agency_id: UUID
) -> Creator | None:
    result = await db.execute(
        select(Creator).where(Creator.id == creator_id, Creator.agency_id == agency_id)
    )
    return result.scalar_one_or_none()


async def _load_brand_target(
    db: AsyncSession, brand_target_id: UUID, agency_id: UUID
) -> BrandTarget | None:
    result = await db.execute(
        select(BrandTarget).where(
            BrandTarget.id == brand_target_id, BrandTarget.agency_id == agency_id
        )
    )
    return result.scalar_one_or_none()


async def _load_contacts(
    db: AsyncSession, contact_ids: list[UUID], agency_id: UUID
) -> list[Contact]:
    result = await db.execute(
        select(Contact).where(
            Contact.id.in_(contact_ids), Contact.agency_id == agency_id
        )
    )
    return list(result.scalars().all())


async def _call_llm(
    creator: Creator,
    brand: BrandTarget,
    contact: Contact,
    has_media_kit: bool,
) -> EmailDraftOutput:
    prompt = PROMPT_TEMPLATE.format(
        creator_name=creator.name,
        creator_bio=creator.bio_summary or "Not available",
        creator_audience_size=creator.audience_size_approx or "Not specified",
        collaboration_types=", ".join(creator.collaboration_types or []) or "Not specified",
        brand_name=brand.company_name,
        brand_domain=brand.company_domain or "Not available",
        brand_reasoning=brand.reasoning or "Strong brand-creator alignment",
        contact_name=contact.full_name,
        contact_title=contact.title or "Unknown",
        has_media_kit="Yes" if has_media_kit else "No",
    )

    return await generate_structured(
        prompt=prompt,
        output_schema=EmailDraftOutput,
        model=QUALITY_MODEL,
        system_instruction=SYSTEM_INSTRUCTION,
    )


async def _save_email(
    db: AsyncSession,
    agency_id: UUID,
    user_id: UUID,
    creator: Creator,
    brand: BrandTarget,
    contact: Contact,
    result: EmailDraftOutput,
    has_media_kit: bool,
) -> None:
    email = OutreachEmail(
        agency_id=agency_id,
        contact_id=contact.id,
        creator_id=creator.id,
        brand_target_id=brand.id,
        drafted_by_user_id=user_id,
        subject=result.subject,
        body=result.body,
        attach_media_kit=has_media_kit,
        status="draft",
    )
    db.add(email)
