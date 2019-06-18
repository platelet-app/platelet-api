"""init

Revision ID: af430d69c868
Revises: 
Create Date: 2019-06-18 21:28:49.785356

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlalchemy_utils

# revision identifiers, used by Alembic.
revision = 'af430d69c868'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('address',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('line1', sa.String(length=64), nullable=True),
    sa.Column('line2', sa.String(length=64), nullable=True),
    sa.Column('town', sa.String(length=64), nullable=True),
    sa.Column('county', sa.String(length=64), nullable=True),
    sa.Column('country', sa.String(length=64), nullable=True),
    sa.Column('postcode', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    op.create_table('delete_flags',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('object_uuid', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('time_to_delete', sa.Integer(), nullable=True),
    sa.Column('time_deleted', sa.DateTime(), nullable=True),
    sa.Column('object_type', sa.Integer(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_delete_flags_time_deleted'), 'delete_flags', ['time_deleted'], unique=False)
    op.create_index(op.f('ix_delete_flags_timestamp'), 'delete_flags', ['timestamp'], unique=False)
    op.create_table('vehicle',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('manufacturer', sa.String(length=64), nullable=True),
    sa.Column('model', sa.String(length=64), nullable=True),
    sa.Column('date_of_manufacture', sa.Date(), nullable=True),
    sa.Column('date_of_registration', sa.Date(), nullable=True),
    sa.Column('registration_number', sa.String(length=10), nullable=True),
    sa.Column('flagged_for_deletion', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_vehicle_timestamp'), 'vehicle', ['timestamp'], unique=False)
    op.create_table('location',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('contact', sa.String(length=64), nullable=True),
    sa.Column('phone_number', sa.Integer(), nullable=True),
    sa.Column('flagged_for_deletion', sa.Boolean(), nullable=True),
    sa.Column('address_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['address_id'], ['address.uuid'], ),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_location_timestamp'), 'location', ['timestamp'], unique=False)
    op.create_table('user',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('address_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sqlalchemy_utils.types.email.EmailType(length=255), nullable=True),
    sa.Column('password', sa.String(), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('dob', sa.Date(), nullable=True),
    sa.Column('assigned_vehicle', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('patch', sa.String(length=64), nullable=True),
    sa.Column('status', sa.String(length=64), nullable=True),
    sa.Column('flagged_for_deletion', sa.Boolean(), nullable=True),
    sa.Column('roles', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
    sa.ForeignKeyConstraint(['address_id'], ['address.uuid'], ),
    sa.ForeignKeyConstraint(['assigned_vehicle'], ['vehicle.uuid'], ),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('username'),
    sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_user_timestamp'), 'user', ['timestamp'], unique=False)
    op.create_table('session',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('flagged_for_deletion', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.uuid'], ),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_session_timestamp'), 'session', ['timestamp'], unique=False)
    op.create_table('task',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('pickup_address_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('dropoff_address_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('patch', sa.String(length=64), nullable=True),
    sa.Column('contact_name', sa.String(length=64), nullable=True),
    sa.Column('contact_number', sa.Integer(), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=True),
    sa.Column('final_duration', sa.Time(), nullable=True),
    sa.Column('miles', sa.Integer(), nullable=True),
    sa.Column('flagged_for_deletion', sa.Boolean(), nullable=True),
    sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['dropoff_address_id'], ['address.uuid'], ),
    sa.ForeignKeyConstraint(['pickup_address_id'], ['address.uuid'], ),
    sa.ForeignKeyConstraint(['session_id'], ['session.uuid'], ),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_task_timestamp'), 'task', ['timestamp'], unique=False)
    op.create_table('deliverable',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('task', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['task'], ['task.uuid'], ),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    op.create_table('note',
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('body', sa.String(length=10000), nullable=True),
    sa.Column('subject', sa.String(length=200), nullable=True),
    sa.Column('task', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('user', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('session', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('vehicle', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('deliverable', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['deliverable'], ['deliverable.uuid'], ),
    sa.ForeignKeyConstraint(['session'], ['session.uuid'], ),
    sa.ForeignKeyConstraint(['task'], ['task.uuid'], ),
    sa.ForeignKeyConstraint(['user'], ['user.uuid'], ),
    sa.ForeignKeyConstraint(['vehicle'], ['vehicle.uuid'], ),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('note')
    op.drop_table('deliverable')
    op.drop_index(op.f('ix_task_timestamp'), table_name='task')
    op.drop_table('task')
    op.drop_index(op.f('ix_session_timestamp'), table_name='session')
    op.drop_table('session')
    op.drop_index(op.f('ix_user_timestamp'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_location_timestamp'), table_name='location')
    op.drop_table('location')
    op.drop_index(op.f('ix_vehicle_timestamp'), table_name='vehicle')
    op.drop_table('vehicle')
    op.drop_index(op.f('ix_delete_flags_timestamp'), table_name='delete_flags')
    op.drop_index(op.f('ix_delete_flags_time_deleted'), table_name='delete_flags')
    op.drop_table('delete_flags')
    op.drop_table('address')
    # ### end Alembic commands ###
