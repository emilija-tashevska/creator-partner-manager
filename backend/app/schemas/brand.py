from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# --- LLM output schemas ---

class BrandSuggestion(BaseModel):
    company_name: str
    company_domain: str | None = None
    reasoning: str
    fit_score: int
    suggested_collab_type: str


class BrandDiscoveryOutput(BaseModel):
    suggestions: list[BrandSuggestion]


# --- API request/response schemas ---

class BrandTargetResponse(BaseModel):
    id: UUID
    agency_id: UUID
    creator_id: UUID
    company_name: str
    company_domain: str | None
    reasoning: str | None
    apollo_organization_id: str | None
    status: str
    scouting_status: str | None
    discovery_round: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BrandDiscoveryStatusResponse(BaseModel):
    status: str  # pending | processing | completed | failed
    discovery_round: int | None = None
    brands_found: int | None = None
