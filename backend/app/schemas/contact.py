from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ContactResponse(BaseModel):
    id: UUID
    agency_id: UUID
    full_name: str
    title: str | None
    company_name: str | None
    email: str
    linkedin_url: str | None
    apollo_person_id: str | None
    has_conflict: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactUpdate(BaseModel):
    full_name: str | None = None
    title: str | None = None
    company_name: str | None = None
    email: str | None = None
    linkedin_url: str | None = None


class ContactWithBrands(ContactResponse):
    """Contact with associated brand target info."""
    brand_names: list[str] = []


class ScoutStatusResponse(BaseModel):
    scouting_status: str  # not_started | in_progress | completed | failed
    contacts_found: int = 0
    has_conflicts: bool = False
