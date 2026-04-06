import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("agency_id", "email", name="uq_contact_agency_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agencies.id"), index=True)

    full_name: Mapped[str] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255))
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    apollo_person_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    has_conflict: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agency = relationship("Agency", back_populates="contacts")
    contact_associations = relationship("ContactAssociation", back_populates="contact")
    outreach_emails = relationship("OutreachEmail", back_populates="contact")
