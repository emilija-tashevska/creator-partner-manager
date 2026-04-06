import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.exceptions import NotFoundError, BadRequestError
from app.database import get_db
from app.models.brand_target import BrandTarget
from app.models.creator import Creator
from app.models.user import User
from app.models.contact import Contact
from app.models.contact_association import ContactAssociation
from app.schemas.brand import BrandTargetResponse, BrandDiscoveryStatusResponse
from app.schemas.contact import ScoutStatusResponse
from app.workers.queue import enqueue

logger = logging.getLogger(__name__)

router = APIRouter(tags=["brands"])


async def _get_creator(
    creator_id: UUID, agency_id: UUID, db: AsyncSession
) -> Creator:
    result = await db.execute(
        select(Creator).where(Creator.id == creator_id, Creator.agency_id == agency_id)
    )
    creator = result.scalar_one_or_none()
    if not creator:
        raise NotFoundError("Creator not found")
    return creator


async def _get_brand(
    brand_id: UUID, agency_id: UUID, db: AsyncSession
) -> BrandTarget:
    result = await db.execute(
        select(BrandTarget).where(
            BrandTarget.id == brand_id, BrandTarget.agency_id == agency_id
        )
    )
    brand = result.scalar_one_or_none()
    if not brand:
        raise NotFoundError("Brand target not found")
    return brand


# --- Discovery endpoints (nested under /creators) ---

@router.post(
    "/creators/{creator_id}/brands/discover",
    response_model=BrandDiscoveryStatusResponse,
    status_code=202,
)
async def trigger_brand_discovery(
    creator_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger LLM brand discovery for a creator. Returns 202 with job info."""
    creator = await _get_creator(creator_id, current_user.agency_id, db)

    if creator.enrichment_status != "completed":
        raise BadRequestError(
            "Creator must be enriched before running brand discovery. "
            "Please wait for enrichment to complete."
        )

    current_max = await db.execute(
        select(sa_func.coalesce(sa_func.max(BrandTarget.discovery_round), 0)).where(
            BrandTarget.creator_id == creator_id
        )
    )
    next_round = current_max.scalar_one() + 1

    await enqueue("run_brand_discovery", str(creator_id), str(current_user.agency_id))
    logger.info(f"Enqueued brand discovery round {next_round} for creator {creator_id}")

    return BrandDiscoveryStatusResponse(
        status="processing",
        discovery_round=next_round,
    )


@router.get(
    "/creators/{creator_id}/brands",
    response_model=list[BrandTargetResponse],
)
async def list_brand_targets(
    creator_id: UUID,
    status: str | None = Query(None, description="Filter by status: suggested, approved, blacklisted"),
    scouting_status: str | None = Query(None, description="Filter by scouting_status"),
    discovery_round: int | None = Query(None, description="Filter by discovery round"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List brand targets for a creator with optional filters."""
    await _get_creator(creator_id, current_user.agency_id, db)

    query = (
        select(BrandTarget)
        .where(
            BrandTarget.creator_id == creator_id,
            BrandTarget.agency_id == current_user.agency_id,
        )
        .order_by(BrandTarget.discovery_round.desc(), BrandTarget.created_at.desc())
    )

    if status:
        query = query.where(BrandTarget.status == status)
    if scouting_status:
        query = query.where(BrandTarget.scouting_status == scouting_status)
    if discovery_round:
        query = query.where(BrandTarget.discovery_round == discovery_round)

    result = await db.execute(query)
    return result.scalars().all()


# --- Brand action endpoints ---

@router.patch("/brands/{brand_id}/approve", response_model=BrandTargetResponse)
async def approve_brand(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a suggested brand target for contact scouting."""
    brand = await _get_brand(brand_id, current_user.agency_id, db)

    if brand.status == "approved":
        raise BadRequestError("Brand is already approved")
    if brand.status == "blacklisted":
        raise BadRequestError("Cannot approve a blacklisted brand. Unblacklist it first.")

    brand.status = "approved"
    brand.scouting_status = "not_started"
    await db.flush()
    await db.refresh(brand)
    return brand


@router.patch("/brands/{brand_id}/blacklist", response_model=BrandTargetResponse)
async def blacklist_brand(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Blacklist a brand — permanently excluded from future discovery."""
    brand = await _get_brand(brand_id, current_user.agency_id, db)

    if brand.status == "blacklisted":
        raise BadRequestError("Brand is already blacklisted")

    brand.status = "blacklisted"
    brand.scouting_status = None
    await db.flush()
    await db.refresh(brand)
    return brand


@router.patch("/brands/{brand_id}/unblacklist", response_model=BrandTargetResponse)
async def unblacklist_brand(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Undo blacklist — sets brand back to suggested."""
    brand = await _get_brand(brand_id, current_user.agency_id, db)

    if brand.status != "blacklisted":
        raise BadRequestError("Brand is not blacklisted")

    brand.status = "suggested"
    brand.scouting_status = None
    await db.flush()
    await db.refresh(brand)
    return brand


# --- Scouting endpoints ---

@router.post("/brands/{brand_id}/scout", response_model=BrandTargetResponse, status_code=202)
async def trigger_scout(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger Apollo contact scouting for an approved brand target."""
    brand = await _get_brand(brand_id, current_user.agency_id, db)

    if brand.status != "approved":
        raise BadRequestError("Brand must be approved before scouting contacts")

    if brand.scouting_status == "in_progress":
        raise BadRequestError("Scouting is already in progress for this brand")

    brand.scouting_status = "in_progress"
    await db.flush()
    await db.refresh(brand)

    await enqueue("run_scout_contacts", str(brand_id), str(current_user.agency_id))
    logger.info(f"Enqueued contact scouting for brand {brand.company_name}")

    return brand


@router.get("/brands/{brand_id}/scout-status", response_model=ScoutStatusResponse)
async def get_scout_status(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll scouting job status for a brand target."""
    brand = await _get_brand(brand_id, current_user.agency_id, db)

    contact_count = 0
    has_conflicts = False

    if brand.scouting_status in ("completed", "in_progress"):
        assoc_result = await db.execute(
            select(sa_func.count(ContactAssociation.id)).where(
                ContactAssociation.brand_target_id == brand_id
            )
        )
        contact_count = assoc_result.scalar_one()

        conflict_result = await db.execute(
            select(sa_func.count(Contact.id))
            .join(ContactAssociation, Contact.id == ContactAssociation.contact_id)
            .where(
                ContactAssociation.brand_target_id == brand_id,
                Contact.has_conflict.is_(True),
            )
        )
        has_conflicts = conflict_result.scalar_one() > 0

    return ScoutStatusResponse(
        scouting_status=brand.scouting_status or "not_started",
        contacts_found=contact_count,
        has_conflicts=has_conflicts,
    )
