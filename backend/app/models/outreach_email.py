import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OutreachEmail(Base):
    __tablename__ = "outreach_emails"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agencies.id"), index=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), index=True)
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("creators.id"), index=True)
    brand_target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand_targets.id"), index=True)
    drafted_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    attach_media_kit: Mapped[bool] = mapped_column(Boolean, default=False)

    # draft | reviewed | pushed_to_gmail | sent | opened | replied
    status: Mapped[str] = mapped_column(String(50), default="draft")
    gmail_draft_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Phase 4 tracking fields (designed for now, used later)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    contact = relationship("Contact", back_populates="outreach_emails")
    creator = relationship("Creator", back_populates="outreach_emails")
    brand_target = relationship("BrandTarget", back_populates="outreach_emails")
