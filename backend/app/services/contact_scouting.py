import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.agency import Agency
from app.models.brand_target import BrandTarget
from app.models.contact import Contact
from app.models.contact_association import ContactAssociation
from app.services.apollo import apollo_client

logger = logging.getLogger(__name__)

TIER_1_TITLES = [
    "Influencer Partnerships Manager",
    "Influencer Relations Manager",
    "Influencer Marketing Manager",
    "Influencer Marketing Coordinator",
]

TIER_2_TITLES = [
    "Creator Partnerships Manager",
    "Creator Relations Manager",
    "Head of Influencer Marketing",
    "Head of Creator Partnerships",
    "Director of Influencer Marketing",
    "Director of Influencer Partnerships",
    "VP of Influencer Marketing",
    "Talent Partnerships Manager",
]

MIN_TIER1_RESULTS = 3


async def scout_contacts(brand_target_id: UUID, agency_id: UUID) -> None:
    """
    Run Apollo scouting for an approved brand target using a tiered approach:
    1. Org enrichment (by domain) → get/cache apollo_organization_id
    2. Tier 1: strict search with 4 precise influencer titles
    3. If < MIN_TIER1_RESULTS, Tier 2: broader search with all 12 titles + fuzzy matching
    4. Dedup contacts by email, create contact_associations
    """
    async with async_session() as db:
        brand = await _load_brand_target(db, brand_target_id, agency_id)
        if not brand:
            logger.error(f"BrandTarget {brand_target_id} not found for scouting")
            return

        brand.scouting_status = "in_progress"
        await db.commit()

        try:
            org_id = await _ensure_org_id(db, brand)
            if not org_id:
                logger.warning(f"No Apollo org found for {brand.company_name} ({brand.company_domain})")
                brand.scouting_status = "completed"
                await db.commit()
                return

            people = await _tiered_people_search(org_id, brand.company_name)

            for person in people:
                await _upsert_contact(db, agency_id, brand.id, person)

            await db.commit()
            brand.scouting_status = "completed"
            await db.commit()

            logger.info(
                f"Scouting completed for brand {brand.company_name}: "
                f"{len(people)} people found"
            )

        except Exception as e:
            logger.error(f"Scouting failed for brand {brand_target_id}: {e}")
            brand.scouting_status = "failed"
            await db.commit()
            raise


async def _tiered_people_search(org_id: str, company_name: str) -> list[dict]:
    """
    Tier 1: Strict search with the 4 most precise influencer titles.
    If fewer than MIN_TIER1_RESULTS come back, Tier 2 expands to all 12 titles
    with fuzzy matching enabled. Deduplicates across both tiers by Apollo person ID.

    The api_search endpoint returns obfuscated data, so each person is then
    enriched via people/match to get full name, email, and LinkedIn.
    """
    logger.info(f"Tier 1 search for {company_name}: {len(TIER_1_TITLES)} titles, strict match")
    tier1_people = await apollo_client.search_people(
        organization_ids=[org_id],
        person_titles=TIER_1_TITLES,
        per_page=10,
        include_similar_titles=False,
    )

    if len(tier1_people) >= MIN_TIER1_RESULTS:
        logger.info(f"Tier 1 returned {len(tier1_people)} results for {company_name} — sufficient")
        return await _enrich_people(tier1_people, company_name)

    logger.info(
        f"Tier 1 returned only {len(tier1_people)} results for {company_name} — "
        f"expanding to Tier 2 with all {len(TIER_1_TITLES) + len(TIER_2_TITLES)} titles"
    )
    all_titles = TIER_1_TITLES + TIER_2_TITLES
    tier2_people = await apollo_client.search_people(
        organization_ids=[org_id],
        person_titles=all_titles,
        per_page=10,
        include_similar_titles=True,
    )

    seen_ids = {p.get("id") for p in tier1_people if p.get("id")}
    merged = list(tier1_people)
    for person in tier2_people:
        pid = person.get("id")
        if pid and pid not in seen_ids:
            merged.append(person)
            seen_ids.add(pid)

    logger.info(f"Tier 1+2 combined: {len(merged)} unique results for {company_name}")
    return await _enrich_people(merged, company_name)


async def _enrich_people(people: list[dict], company_name: str) -> list[dict]:
    """Enrich each person from the search results to get full contact details."""
    enriched = []
    for person in people:
        person_id = person.get("id")
        if not person_id:
            continue
        full_person = await apollo_client.enrich_person(person_id)
        if full_person and full_person.get("email"):
            enriched.append(full_person)
    logger.info(f"Enriched {len(enriched)}/{len(people)} people with emails for {company_name}")
    return enriched


async def _load_brand_target(
    db: AsyncSession, brand_target_id: UUID, agency_id: UUID
) -> BrandTarget | None:
    result = await db.execute(
        select(BrandTarget).where(
            BrandTarget.id == brand_target_id,
            BrandTarget.agency_id == agency_id,
        )
    )
    return result.scalar_one_or_none()


async def _load_agency(db: AsyncSession, agency_id: UUID) -> Agency:
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    return result.scalar_one()


async def _ensure_org_id(db: AsyncSession, brand: BrandTarget) -> str | None:
    """Get or fetch the Apollo organization ID for a brand target."""
    if brand.apollo_organization_id:
        return brand.apollo_organization_id

    if not brand.company_domain:
        logger.info(f"No domain for brand {brand.company_name}, cannot enrich org")
        return None

    org_data = await apollo_client.enrich_organization(brand.company_domain)
    if not org_data:
        return None

    org_id = org_data.get("id")
    if org_id:
        brand.apollo_organization_id = org_id
        await db.commit()

    return org_id


async def _upsert_contact(
    db: AsyncSession,
    agency_id: UUID,
    brand_target_id: UUID,
    person: dict,
) -> None:
    """
    Insert or match a contact from Apollo data.
    Dedup by (agency_id, email). Flag conflicts when apollo_person_id mismatches.
    """
    email = person.get("email")
    if not email:
        return

    apollo_person_id = person.get("id")
    full_name = person.get("name", "Unknown")
    title = person.get("title")
    company_name = person.get("organization", {}).get("name") if person.get("organization") else None
    linkedin_url = person.get("linkedin_url")

    existing = await db.execute(
        select(Contact).where(Contact.agency_id == agency_id, Contact.email == email)
    )
    contact = existing.scalar_one_or_none()

    if contact:
        if contact.apollo_person_id and contact.apollo_person_id != apollo_person_id:
            contact.has_conflict = True
            logger.warning(
                f"Conflict detected for {email}: existing person_id={contact.apollo_person_id}, "
                f"new person_id={apollo_person_id}"
            )
    else:
        contact = Contact(
            agency_id=agency_id,
            full_name=full_name,
            title=title,
            company_name=company_name,
            email=email,
            linkedin_url=linkedin_url,
            apollo_person_id=apollo_person_id,
        )
        db.add(contact)
        await db.flush()

    assoc_exists = await db.execute(
        select(ContactAssociation).where(
            ContactAssociation.contact_id == contact.id,
            ContactAssociation.brand_target_id == brand_target_id,
        )
    )
    if not assoc_exists.scalar_one_or_none():
        db.add(ContactAssociation(
            contact_id=contact.id,
            brand_target_id=brand_target_id,
        ))
