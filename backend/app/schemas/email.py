from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# --- LLM output schema ---

class EmailDraftOutput(BaseModel):
    subject: str
    body: str


# --- API request/response schemas ---

class EmailDraftRequest(BaseModel):
    contact_ids: list[UUID]
    creator_id: UUID
    brand_target_id: UUID


class EmailUpdateRequest(BaseModel):
    subject: str | None = None
    body: str | None = None
    attach_media_kit: bool | None = None


class EmailResponse(BaseModel):
    id: UUID
    agency_id: UUID
    contact_id: UUID
    creator_id: UUID
    brand_target_id: UUID
    drafted_by_user_id: UUID
    subject: str
    body: str
    attach_media_kit: bool
    status: str
    gmail_draft_id: str | None
    sent_at: datetime | None
    opened_at: datetime | None
    replied_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Denormalized fields for display
    contact_name: str | None = None
    contact_email: str | None = None
    contact_title: str | None = None
    brand_name: str | None = None

    model_config = {"from_attributes": True}


class EmailDraftStatusResponse(BaseModel):
    status: str  # processing | completed | failed
    emails_drafted: int = 0


class EmailBulkPushRequest(BaseModel):
    email_ids: list[UUID]


class EmailPushResponse(BaseModel):
    id: UUID
    status: str
    gmail_draft_id: str | None


class EmailBulkPushResponse(BaseModel):
    pushed: int = 0
    failed: int = 0
    results: list[EmailPushResponse] = []
