"""priorities foreign key for tasks

Revision ID: f4790c61165f
Revises: b96170218340
Create Date: 2019-10-19 17:23:28.768309

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4790c61165f'
down_revision = 'b96170218340'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('priority', sa.Column('label', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('priority', 'label')
    # ### end Alembic commands ###