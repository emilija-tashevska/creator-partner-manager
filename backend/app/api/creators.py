import logging
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.exceptions import NotFoundError, BadRequestError
from app.database import get_db
from app.models.creator import Creator
from app.models.user import User
from app.schemas.creator import (
    CreatorCreate,
    CreatorUpdate,
    CreatorStatusUpdate,
    CreatorResponse,
    CreatorListResponse,
)
from app.services.file_storage import save_upload
from app.workers.queue import enqueue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/creators", tags=["creators"])

VALID_PROFILE_STATUSES = {"draft", "reviewed", "active"}


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


@router.post("", response_model=CreatorResponse, status_code=201)
async def create_creator(
    body: CreatorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    creator = Creator(
        agency_id=current_user.agency_id,
        **body.model_dump(),
    )
    db.add(creator)
    await db.flush()
    await db.refresh(creator)

    await enqueue(
        "run_enrichment",
        str(creator.id),
        str(current_user.agency_id),
    )
    logger.info(f"Enqueued enrichment for creator {creator.id}")

    return creator


@router.get("", response_model=list[CreatorListResponse])
async def list_creators(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Creator)
        .where(Creator.agency_id == current_user.agency_id)
        .order_by(Creator.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{creator_id}", response_model=CreatorResponse)
async def get_creator(
    creator_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_creator(creator_id, current_user.agency_id, db)


@router.patch("/{creator_id}", response_model=CreatorResponse)
async def update_creator(
    creator_id: UUID,
    body: CreatorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    creator = await _get_creator(creator_id, current_user.agency_id, db)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(creator, field, value)

    await db.flush()
    await db.refresh(creator)
    return creator


@router.patch("/{creator_id}/status", response_model=CreatorResponse)
async def update_creator_status(
    creator_id: UUID,
    body: CreatorStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.profile_status not in VALID_PROFILE_STATUSES:
        raise BadRequestError(f"Invalid status. Must be one of: {VALID_PROFILE_STATUSES}")

    creator = await _get_creator(creator_id, current_user.agency_id, db)
    creator.profile_status = body.profile_status
    await db.flush()
    await db.refresh(creator)
    return creator


@router.post("/{creator_id}/enrich", response_model=CreatorResponse)
async def enrich_creator(
    creator_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-trigger LLM enrichment for a creator."""
    creator = await _get_creator(creator_id, current_user.agency_id, db)
    creator.enrichment_status = "pending"
    await db.flush()
    await db.refresh(creator)

    await enqueue("run_enrichment", str(creator.id), str(current_user.agency_id))
    logger.info(f"Enqueued re-enrichment for creator {creator.id}")

    return creator


@router.post("/{creator_id}/media-kit", response_model=CreatorResponse)
async def upload_media_kit(
    creator_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    creator = await _get_creator(creator_id, current_user.agency_id, db)

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise BadRequestError("Only PDF files are accepted")

    path = await save_upload(file, str(current_user.agency_id), str(creator_id))
    creator.media_kit_file_path = path
    await db.flush()
    await db.refresh(creator)
    return creator
