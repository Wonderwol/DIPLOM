"""Add username field

Revision ID: 10ef57aaf71c
Revises: bb52a9a9ea1a
Create Date: 2025-05-25 04:32:02.720886

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '10ef57aaf71c'
down_revision = 'bb52a9a9ea1a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=100), nullable=False))
        batch_op.add_column(sa.Column('username', sa.String(length=100), nullable=False))
        batch_op.drop_constraint('users_email_key', type_='unique')
        batch_op.create_unique_constraint(None, ['username'])
        batch_op.drop_column('email')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.VARCHAR(length=120), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='unique')
        batch_op.create_unique_constraint('users_email_key', ['email'])
        batch_op.drop_column('username')
        batch_op.drop_column('name')

    # ### end Alembic commands ###
