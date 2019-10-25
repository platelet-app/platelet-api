"""deliverable types model and foreign key on deliverable

Revision ID: b70ad3f5fc78
Revises: 1b5ecd4a7405
Create Date: 2019-10-25 20:52:08.203314

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b70ad3f5fc78'
down_revision = '1b5ecd4a7405'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('deliverable_type',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.add_column('deliverable', sa.Column('type_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'deliverable', 'deliverable_type', ['type_id'], ['id'])
    op.drop_column('deliverable', 'name')
    op.create_unique_constraint(None, 'user', ['display_name'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='unique')
    op.add_column('deliverable', sa.Column('name', sa.VARCHAR(length=64), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'deliverable', type_='foreignkey')
    op.drop_column('deliverable', 'type_id')
    op.drop_table('deliverable_type')
    # ### end Alembic commands ###
