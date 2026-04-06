from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreatorCreate(BaseModel):
    name: str
    instagram_handle: str | None = None
    tiktok_handle: str | None = None
    youtube_handle: str | None = None
    x_handle: str | None = None
    content_links: list[str] = []
    niche: str | None = None
    audience_size_approx: str | None = None
    media_kit_url: str | None = None
    notes: str | None = None


class CreatorUpdate(BaseModel):
    name: str | None = None
    instagram_handle: str | None = None
    tiktok_handle: str | None = None
    youtube_handle: str | None = None
    x_handle: str | None = None
    content_links: list[str] | None = None
    niche: str | None = None
    audience_size_approx: str | None = None
    media_kit_url: str | None = None
    bio_summary: str | None = None
    content_style: str | None = None
    audience_demographics: dict | None = None
    tone_descriptors: list[str] | None = None
    collaboration_types: list[str] | None = None
    collaboration_verticals: list[str] | None = None
    notes: str | None = None


class CreatorStatusUpdate(BaseModel):
    profile_status: str  # draft | reviewed | active


class AudienceDemographics(BaseModel):
    age_range: str | None = None
    gender_split: str | None = None
    primary_regions: list[str] = []
    interests: list[str] = []

    model_config = {"from_attributes": True}


class CreatorResponse(BaseModel):
    id: UUID
    agency_id: UUID
    name: str
    instagram_handle: str | None
    tiktok_handle: str | None
    youtube_handle: str | None
    x_handle: str | None
    content_links: list[str] | None
    niche: str | None
    audience_size_approx: str | None
    media_kit_url: str | None
    media_kit_file_path: str | None
    bio_summary: str | None
    content_style: str | None
    audience_demographics: dict | None
    tone_descriptors: list[str] | None
    collaboration_types: list[str] | None
    collaboration_verticals: list[str] | None
    enrichment_status: str
    profile_status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreatorListResponse(BaseModel):
    id: UUID
    name: str
    niche: str | None
    audience_size_approx: str | None
    enrichment_status: str
    profile_status: str
    instagram_handle: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
