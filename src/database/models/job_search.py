"""JobSearch model definition."""

import uuid

from sqlalchemy import Boolean, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base
from src.database.models.mixins import TimestampMixin


class JobSearch(TimestampMixin, Base):
    """Shared job search entity."""

    __tablename__ = "job_searches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    municipality: Mapped[str] = mapped_column(String(100), nullable=False)
    remote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_job_searches_keyword", "keyword"),
        Index("ix_job_searches_state", "state"),
        Index("ix_job_searches_municipality", "municipality"),
        Index("ix_job_searches_active", "active"),
    )
