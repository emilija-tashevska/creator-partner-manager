import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Creator(Base):
    __tablename__ = "creators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agencies.id"), index=True)

    # Basic info (user-provided)
    name: Mapped[str] = mapped_column(String(255))
    instagram_handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tiktok_handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    youtube_handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    x_handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_links: Mapped[list | None] = mapped_column(JSONB, default=list)
    niche: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audience_size_approx: Mapped[str | None] = mapped_column(String(100), nullable=True)
    media_kit_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_kit_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Enriched fields (AI-generated, editable by human)
    bio_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_style: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience_demographics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tone_descriptors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    collaboration_types: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    collaboration_verticals: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Status tracking
    enrichment_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending | processing | completed | failed
    profile_status: Mapped[str] = mapped_column(String(50), default="draft")  # draft | reviewed | active

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agency = relationship("Agency", back_populates="creators")
    brand_targets = relationship("BrandTarget", back_populates="creator")
    outreach_emails = relationship("OutreachEmail", back_populates="creator")
