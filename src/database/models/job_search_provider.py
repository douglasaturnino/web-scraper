"""JobSearchProvider model definition."""

import uuid

from sqlalchemy import Boolean, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base
from src.database.models.mixins import TimestampMixin


class JobSearchProvider(TimestampMixin, Base):
    """Association between job searches and providers."""

    __tablename__ = "job_search_providers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    search_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint(
            "search_id",
            "provider",
            name="uq_job_search_providers_search_id_provider",
        ),
        Index("ix_job_search_providers_search_id", "search_id"),
        Index("ix_job_search_providers_provider", "provider"),
        Index("ix_job_search_providers_active", "active"),
    )
