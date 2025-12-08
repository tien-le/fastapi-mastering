"""Added ForeignKey user_id

Revision ID: 7a6fb7c5039a
Revises: f6fa61e85818
Create Date: 2025-12-08 10:29:17.587701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a6fb7c5039a'
down_revision: Union[str, Sequence[str], None] = 'f6fa61e85818'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite can't ALTER constraints in-place; use batch_alter_table so Alembic
    # recreates the tables under the hood.
    with op.batch_alter_table("comments", recreate="always") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=False))
        # Recreate indexes (old ones are dropped during the table rewrite)
        batch.create_index("ix_comments_post_id", ["post_id"], unique=False)
        batch.create_index("ix_comments_user_id", ["user_id"], unique=False)
        batch.create_foreign_key(
            "fk_comments_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_foreign_key(
            "fk_comments_post_id_posts",
            "posts",
            ["post_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("posts", recreate="always") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=False))
        batch.create_index("ix_posts_user_id", ["user_id"], unique=False)
        batch.create_foreign_key(
            "fk_posts_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("users", recreate="always") as batch:
        batch.drop_index("ix_users_email")
        batch.create_unique_constraint("uq_users_email", ["email"])


def downgrade() -> None:
    """Downgrade schema."""
    # Mirror the upgrade structure for SQLite compatibility.
    with op.batch_alter_table("users", recreate="always") as batch:
        batch.drop_constraint("uq_users_email", type_="unique")
        batch.create_index("ix_users_email", ["email"], unique=True)

    with op.batch_alter_table("posts", recreate="always") as batch:
        batch.drop_constraint("fk_posts_user_id_users", type_="foreignkey")
        batch.drop_index("ix_posts_user_id")
        batch.drop_column("user_id")

    with op.batch_alter_table("comments", recreate="always") as batch:
        batch.drop_constraint("fk_comments_user_id_users", type_="foreignkey")
        batch.drop_constraint("fk_comments_post_id_posts", type_="foreignkey")
        batch.drop_index("ix_comments_user_id")
        batch.drop_index("ix_comments_post_id")
        batch.drop_column("user_id")
