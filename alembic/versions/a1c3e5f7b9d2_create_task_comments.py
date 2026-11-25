"""create_task_comments

Revision ID: a1c3e5f7b9d2
Revises:
Create Date: 2026-10-28 00:00:00.000000

Hand-written, scoped to `task_comments` only. The repo has no baseline
migration, so this assumes `users` and `tasks` already exist (FK targets).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1c3e5f7b9d2"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "task_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "is_deleted", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_task_comments_author_id"), "task_comments", ["author_id"], unique=False
    )
    op.create_index(
        "ix_task_comments_task_id_is_deleted_created_at",
        "task_comments",
        ["task_id", "is_deleted", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_task_comments_task_id_is_deleted_created_at", table_name="task_comments"
    )
    op.drop_index(op.f("ix_task_comments_author_id"), table_name="task_comments")
    op.drop_table("task_comments")
