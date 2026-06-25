"""baseline — create the full schema from the SQLAlchemy models.

Pragmatic baseline: builds every table from Base.metadata (the single source of
truth in app/models). Later migrations use `alembic revision --autogenerate`.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-25
"""
from alembic import op

from app.core.db import Base
import app.models  # noqa: F401  — register all tables

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
