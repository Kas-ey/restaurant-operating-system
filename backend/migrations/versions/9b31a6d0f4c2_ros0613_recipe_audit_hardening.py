"""ros0613_recipe_audit_hardening

Revision ID: 9b31a6d0f4c2
Revises: 32c6534227ef
Create Date: 2026-07-17 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9b31a6d0f4c2"
down_revision = "32c6534227ef"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recipe_audit_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("requested_by", sa.String(length=64), nullable=False),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("organization_id", sa.String(length=64), nullable=True),
        sa.Column("branch_id", sa.String(length=64), nullable=True),
        sa.Column("recipe_id", sa.String(length=64), nullable=True),
        sa.Column("recipe_version_id", sa.String(length=64), nullable=True),
        sa.Column("secret_formulation_id", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("event_metadata", sa.Text(), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["secret_formulation_id"], ["secret_formulations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("recipe_audit_events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_recipe_audit_events_branch_id"), ["branch_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_recipe_audit_events_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_recipe_audit_events_event_timestamp"), ["event_timestamp"], unique=False)
        batch_op.create_index(batch_op.f("ix_recipe_audit_events_event_type"), ["event_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_recipe_audit_events_organization_id"), ["organization_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_recipe_audit_events_recipe_id"), ["recipe_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_recipe_audit_events_recipe_version_id"), ["recipe_version_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_recipe_audit_events_requested_by"), ["requested_by"], unique=False)
        batch_op.create_index(batch_op.f("ix_recipe_audit_events_secret_formulation_id"), ["secret_formulation_id"], unique=False)


def downgrade():
    with op.batch_alter_table("recipe_audit_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_recipe_audit_events_secret_formulation_id"))
        batch_op.drop_index(batch_op.f("ix_recipe_audit_events_requested_by"))
        batch_op.drop_index(batch_op.f("ix_recipe_audit_events_recipe_version_id"))
        batch_op.drop_index(batch_op.f("ix_recipe_audit_events_recipe_id"))
        batch_op.drop_index(batch_op.f("ix_recipe_audit_events_organization_id"))
        batch_op.drop_index(batch_op.f("ix_recipe_audit_events_event_type"))
        batch_op.drop_index(batch_op.f("ix_recipe_audit_events_event_timestamp"))
        batch_op.drop_index(batch_op.f("ix_recipe_audit_events_created_at"))
        batch_op.drop_index(batch_op.f("ix_recipe_audit_events_branch_id"))
    op.drop_table("recipe_audit_events")
