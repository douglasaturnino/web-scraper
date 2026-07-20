"""Create job_searches, vacancies and job_search_providers tables.

Revision ID: cae944d4b475
Revises:
Create Date: 2026-07-20 12:27:06.112684

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cae944d4b475"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP TABLE IF EXISTS job_searches")
    op.create_table(
        "job_search_providers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("search_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "search_id",
            "provider",
            name="uq_job_search_providers_search_id_provider",
        ),
    )
    op.create_index(
        "ix_job_search_providers_active",
        "job_search_providers",
        ["active"],
        unique=False,
    )
    op.create_index(
        "ix_job_search_providers_provider",
        "job_search_providers",
        ["provider"],
        unique=False,
    )
    op.create_index(
        "ix_job_search_providers_search_id",
        "job_search_providers",
        ["search_id"],
        unique=False,
    )
    op.create_table(
        "job_searches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("keyword", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("municipality", sa.String(length=100), nullable=False),
        sa.Column("remote", sa.Boolean(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_searches_active", "job_searches", ["active"], unique=False)
    op.create_index(
        "ix_job_searches_keyword", "job_searches", ["keyword"], unique=False
    )
    op.create_index(
        "ix_job_searches_municipality",
        "job_searches",
        ["municipality"],
        unique=False,
    )
    op.create_index("ix_job_searches_state", "job_searches", ["state"], unique=False)
    op.create_table(
        "vacancies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("publication_date", sa.DateTime(), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("municipality", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("collected_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "external_id",
            "url",
            name="uq_vacancies_provider_external_id_url",
        ),
    )
    op.create_index(
        "ix_vacancies_external_id", "vacancies", ["external_id"], unique=False
    )
    op.create_index("ix_vacancies_provider", "vacancies", ["provider"], unique=False)
    op.create_index(
        "ix_vacancies_publication_date",
        "vacancies",
        ["publication_date"],
        unique=False,
    )
    op.create_index("ix_vacancies_url", "vacancies", ["url"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_vacancies_url", table_name="vacancies")
    op.drop_index("ix_vacancies_publication_date", table_name="vacancies")
    op.drop_index("ix_vacancies_provider", table_name="vacancies")
    op.drop_index("ix_vacancies_external_id", table_name="vacancies")
    op.drop_table("vacancies")
    op.drop_index("ix_job_searches_state", table_name="job_searches")
    op.drop_index("ix_job_searches_municipality", table_name="job_searches")
    op.drop_index("ix_job_searches_keyword", table_name="job_searches")
    op.drop_index("ix_job_searches_active", table_name="job_searches")
    op.drop_table("job_searches")
    op.drop_index(
        "ix_job_search_providers_search_id", table_name="job_search_providers"
    )
    op.drop_index("ix_job_search_providers_provider", table_name="job_search_providers")
    op.drop_index("ix_job_search_providers_active", table_name="job_search_providers")
    op.drop_table("job_search_providers")
    op.create_table(
        "job_searches",
        sa.Column("id", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("userId", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column(
            "keyword",
            sa.VARCHAR(length=255),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("city", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("remote", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("active", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("createdAt", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_searches_id"), "job_searches", ["id"], unique=False)
