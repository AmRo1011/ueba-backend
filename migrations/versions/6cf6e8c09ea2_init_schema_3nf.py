"""init schema 3NF

Revision ID: 6cf6e8c09ea2
Revises: 
Create Date: 2025-10-23 18:22:53.070262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6cf6e8c09ea2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from alembic import op
    import sqlalchemy as sa
    from sqlalchemy import text

    # ===== Lookups ????? =====
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False, unique=True),
        sa.Column('name', sa.String(length=64), nullable=False),
    )

    op.create_table(
        'activity_types',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False, unique=True),
        sa.Column('name', sa.String(length=128), nullable=False),
    )

    op.create_table(
        'anomaly_types',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False, unique=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('severity_default', sa.Integer(), server_default=sa.text("1"), nullable=False),
    )

    # ===== Core: users ?? logs ?? anomalies =====
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('uid', sa.String(length=64), nullable=False),
        sa.Column('username', sa.String(length=128), nullable=True),
        sa.Column('email', sa.String(length=128), nullable=True),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id'), nullable=True),
        sa.Column('risk_score', sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column('anomaly_count', sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index('ix_users_uid', 'users', ['uid'], unique=True)

    op.create_table(
        'logs',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('activity_type_id', sa.Integer(), sa.ForeignKey('activity_types.id'), nullable=False),
        sa.Column('source_ip', sa.String(length=64), nullable=True),
        sa.Column('params_json', sa.JSON(), nullable=True),
        sa.Column('hour', sa.Integer(), nullable=True),
        sa.Column('is_weekend', sa.Boolean(), nullable=True),
        sa.Column('is_night', sa.Boolean(), nullable=True),
    )
    op.create_index('ix_logs_user_ts', 'logs', ['user_id', 'ts'])
    op.create_index('ix_logs_activity_ts', 'logs', ['activity_type_id', 'ts'])
    op.create_index('ix_logs_user_id', 'logs', ['user_id'])

    op.create_table(
        'anomalies',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('anomaly_type_id', sa.Integer(), sa.ForeignKey('anomaly_types.id'), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('risk', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=16), server_default=sa.text("'open'"), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('evidence_json', sa.JSON(), nullable=True),
    )
    op.create_index('ix_anom_user_status', 'anomalies', ['user_id', 'status'])
    op.create_index('ix_anom_type_ts', 'anomalies', ['anomaly_type_id', 'detected_at'])


def downgrade() -> None:
    from alembic import op

    # ??? ???????
    op.drop_index('ix_anom_type_ts', table_name='anomalies')
    op.drop_index('ix_anom_user_status', table_name='anomalies')
    op.drop_table('anomalies')

    op.drop_index('ix_logs_user_id', table_name='logs')
    op.drop_index('ix_logs_activity_ts', table_name='logs')
    op.drop_index('ix_logs_user_ts', table_name='logs')
    op.drop_table('logs')

    op.drop_index('ix_users_uid', table_name='users')
    op.drop_table('users')

    op.drop_table('anomaly_types')
    op.drop_table('activity_types')
    op.drop_table('roles')

