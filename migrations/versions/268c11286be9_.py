"""

Revision ID: 268c11286be9
Revises: 
Create Date: 2018-11-21 23:41:30.276652

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '268c11286be9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('passwordHash', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_user_timestamp'), 'user', ['timestamp'], unique=False)
    op.create_table('vehicle',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('manufacturer', sa.String(length=64), nullable=True),
    sa.Column('model', sa.String(length=64), nullable=True),
    sa.Column('dateOfManufacture', sa.Date(), nullable=True),
    sa.Column('dateOfRegistration', sa.Date(), nullable=True),
    sa.Column('registrationNumber', sa.String(length=10), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_timestamp'), 'vehicle', ['timestamp'], unique=False)
    op.create_table('rider',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('address1', sa.String(length=64), nullable=True),
    sa.Column('address2', sa.String(length=64), nullable=True),
    sa.Column('town', sa.String(length=64), nullable=True),
    sa.Column('county', sa.String(length=64), nullable=True),
    sa.Column('country', sa.String(length=64), nullable=True),
    sa.Column('postcode', sa.String(length=7), nullable=True),
    sa.Column('dob', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=64), nullable=True),
    sa.Column('assignedVehicle', sa.Integer(), nullable=True),
    sa.Column('patch', sa.String(length=64), nullable=True),
    sa.ForeignKeyConstraint(['assignedVehicle'], ['vehicle.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rider_timestamp'), 'rider', ['timestamp'], unique=False)
    op.create_table('session',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_session_timestamp'), 'session', ['timestamp'], unique=False)
    op.create_table('task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('pickupAddress1', sa.String(length=64), nullable=True),
    sa.Column('pickupAddress2', sa.String(length=64), nullable=True),
    sa.Column('pickupTown', sa.String(length=64), nullable=True),
    sa.Column('pickupPostcode', sa.String(length=7), nullable=True),
    sa.Column('destinationAddress1', sa.String(length=64), nullable=True),
    sa.Column('destinationAddress2', sa.String(length=64), nullable=True),
    sa.Column('destinationTown', sa.String(length=64), nullable=True),
    sa.Column('destinationPostcode', sa.String(length=7), nullable=True),
    sa.Column('patch', sa.String(length=64), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=True),
    sa.Column('finalDuration', sa.Time(), nullable=True),
    sa.Column('miles', sa.Integer(), nullable=True),
    sa.Column('session', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['session'], ['session.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_timestamp'), 'task', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_task_timestamp'), table_name='task')
    op.drop_table('task')
    op.drop_index(op.f('ix_session_timestamp'), table_name='session')
    op.drop_table('session')
    op.drop_index(op.f('ix_rider_timestamp'), table_name='rider')
    op.drop_table('rider')
    op.drop_index(op.f('ix_vehicle_timestamp'), table_name='vehicle')
    op.drop_table('vehicle')
    op.drop_index(op.f('ix_user_timestamp'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###
