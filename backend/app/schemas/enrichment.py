from pydantic import BaseModel


class AudienceDemographics(BaseModel):
    age_range: str
    gender_split: str
    primary_regions: list[str]
    interests: list[str]


class CreatorEnrichmentOutput(BaseModel):
    bio_summary: str
    content_style: str
    audience_demographics: AudienceDemographics
    tone_descriptors: list[str]
    collaboration_types: list[str]
    collaboration_verticals: list[str]
    confidence_note: str
