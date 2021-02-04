"""protected field on Address

Revision ID: 427743e76984
Revises: f8c342997aab
Create Date: 2021-02-02 11:39:45.955233

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '427743e76984'
down_revision = 'f8c342997aab'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('address', sa.Column('protected', sa.Boolean(), nullable=True))
    op.drop_column('location', 'protected')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('location', sa.Column('protected', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('address', 'protected')
    # ### end Alembic commands ###
