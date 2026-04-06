import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models.brand_target import BrandTarget
from app.models.contact import Contact
from app.models.contact_association import ContactAssociation
from app.models.user import User
from app.schemas.contact import ContactResponse, ContactUpdate, ContactWithBrands

logger = logging.getLogger(__name__)

router = APIRouter(tags=["contacts"])


@router.get("/creators/{creator_id}/contacts", response_model=list[ContactWithBrands])
async def list_creator_contacts(
    creator_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """All contacts for a creator, via brand_target -> contact_associations."""
    result = await db.execute(
        select(Contact)
        .join(ContactAssociation, Contact.id == ContactAssociation.contact_id)
        .join(BrandTarget, ContactAssociation.brand_target_id == BrandTarget.id)
        .where(
            BrandTarget.creator_id == creator_id,
            BrandTarget.agency_id == current_user.agency_id,
        )
        .options(selectinload(Contact.contact_associations).selectinload(ContactAssociation.brand_target))
        .distinct()
    )
    contacts = result.scalars().all()

    response = []
    for contact in contacts:
        brand_names = [
            assoc.brand_target.company_name
            for assoc in contact.contact_associations
            if assoc.brand_target.creator_id == creator_id
        ]
        contact_data = ContactWithBrands.model_validate(contact)
        contact_data.brand_names = brand_names
        response.append(contact_data)

    return response


@router.get("/brands/{brand_id}/contacts", response_model=list[ContactResponse])
async def list_brand_contacts(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Contacts for a specific brand target."""
    result = await db.execute(
        select(Contact)
        .join(ContactAssociation, Contact.id == ContactAssociation.contact_id)
        .where(
            ContactAssociation.brand_target_id == brand_id,
            Contact.agency_id == current_user.agency_id,
        )
        .order_by(Contact.full_name)
    )
    return result.scalars().all()


@router.get("/contacts/{contact_id}", response_model=ContactWithBrands)
async def get_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Single contact detail with all brand_target associations."""
    result = await db.execute(
        select(Contact)
        .where(Contact.id == contact_id, Contact.agency_id == current_user.agency_id)
        .options(selectinload(Contact.contact_associations).selectinload(ContactAssociation.brand_target))
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise NotFoundError("Contact not found")

    brand_names = [assoc.brand_target.company_name for assoc in contact.contact_associations]
    contact_data = ContactWithBrands.model_validate(contact)
    contact_data.brand_names = brand_names
    return contact_data


@router.patch("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    body: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually update a contact (e.g. to resolve conflicts)."""
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id, Contact.agency_id == current_user.agency_id
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise NotFoundError("Contact not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    if contact.has_conflict and update_data:
        contact.has_conflict = False

    await db.flush()
    await db.refresh(contact)
    return contact


@router.get("/contacts/duplicates", response_model=list[ContactResponse])
async def list_conflict_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List contacts flagged with has_conflict=true for manual resolution."""
    result = await db.execute(
        select(Contact)
        .where(
            Contact.agency_id == current_user.agency_id,
            Contact.has_conflict.is_(True),
        )
        .order_by(Contact.created_at.desc())
    )
    return result.scalars().all()
