"""Добавлено поле уровня активности

Revision ID: a7f0e3db632c
Revises: b8581a4cb024
Create Date: 2025-06-01 03:18:22.356724

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7f0e3db632c'
down_revision = 'b8581a4cb024'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('activity_level', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('activity_level')

    # ### end Alembic commands ###
