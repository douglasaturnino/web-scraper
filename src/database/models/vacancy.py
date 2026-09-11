"""Vacancy model definition."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base
from src.database.models.mixins import TimestampMixin


class Vacancy(TimestampMixin, Base):
    """Collected job vacancy entity."""

    __tablename__ = "vacancies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    publication_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    municipality: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_id",
            "url",
            name="uq_vacancies_provider_external_id_url",
        ),
        Index("ix_vacancies_provider", "provider"),
        Index("ix_vacancies_external_id", "external_id"),
        Index("ix_vacancies_url", "url"),
        Index("ix_vacancies_publication_date", "publication_date"),
    )
