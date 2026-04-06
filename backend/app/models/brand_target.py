import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BrandTarget(Base):
    __tablename__ = "brand_targets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agencies.id"), index=True)
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("creators.id"), index=True)

    company_name: Mapped[str] = mapped_column(String(255))
    company_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    apollo_organization_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Suggestion lifecycle: suggested | approved | blacklisted
    status: Mapped[str] = mapped_column(String(50), default="suggested")
    # Scouting lifecycle (only relevant once approved): not_started | in_progress | completed | failed
    scouting_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Which LLM discovery batch produced this suggestion
    discovery_round: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    creator = relationship("Creator", back_populates="brand_targets")
    contact_associations = relationship("ContactAssociation", back_populates="brand_target")
    outreach_emails = relationship("OutreachEmail", back_populates="brand_target")
