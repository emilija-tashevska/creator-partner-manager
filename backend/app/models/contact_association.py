import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ContactAssociation(Base):
    __tablename__ = "contact_associations"
    __table_args__ = (
        UniqueConstraint("contact_id", "brand_target_id", name="uq_contact_brand_target"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), index=True)
    brand_target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brand_targets.id"), index=True)
    scouted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contact = relationship("Contact", back_populates="contact_associations")
    brand_target = relationship("BrandTarget", back_populates="contact_associations")
