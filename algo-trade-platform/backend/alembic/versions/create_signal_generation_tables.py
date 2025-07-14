"""create signal generation tables

Revision ID: create_signal_generation_tables
Revises: 
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_signal_generation_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create enum types
    op.execute("CREATE TYPE exchangetype AS ENUM ('NYSE', 'NASDAQ', 'CBOE', 'SMART')")
    op.execute("CREATE TYPE ordertype AS ENUM ('STOP', 'STOP_LIMIT', 'MARKET', 'LIMIT')")
    op.execute("CREATE TYPE producttype AS ENUM ('MARGIN', 'CASH')")
    op.execute("CREATE TYPE orderside AS ENUM ('BUY', 'SELL')")
    op.execute("CREATE TYPE signalstatus AS ENUM ('PENDING', 'VALIDATED', 'EXECUTED', 'CANCELLED', 'FAILED')")

    # Create signal_generation table
    op.create_table(
        'signal_generation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', postgresql.ENUM('NYSE', 'NASDAQ', 'CBOE', 'SMART', name='exchangetype'), nullable=False),
        sa.Column('order_type', postgresql.ENUM('STOP', 'STOP_LIMIT', 'MARKET', 'LIMIT', name='ordertype'), nullable=False),
        sa.Column('product_type', postgresql.ENUM('MARGIN', 'CASH', name='producttype'), nullable=False),
        sa.Column('side', postgresql.ENUM('BUY', 'SELL', name='orderside'), nullable=False),
        sa.Column('contract_size', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=True),
        sa.Column('stop_loss', sa.Float(), nullable=True),
        sa.Column('take_profit', sa.Float(), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'VALIDATED', 'EXECUTED', 'CANCELLED', 'FAILED', name='signalstatus'), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_signal_generation_id'), 'signal_generation', ['id'], unique=False)
    op.create_index(op.f('ix_signal_generation_user_id'), 'signal_generation', ['user_id'], unique=False)
    op.create_index(op.f('ix_signal_generation_strategy_id'), 'signal_generation', ['strategy_id'], unique=False)

    # Add constraints
    op.create_check_constraint(
        'check_contract_size_positive',
        'signal_generation',
        'contract_size > 0'
    )
    op.create_check_constraint(
        'check_quantity_positive',
        'signal_generation',
        'quantity > 0'
    )
    op.create_check_constraint(
        'check_entry_price_positive',
        'signal_generation',
        'entry_price > 0'
    )
    op.create_check_constraint(
        'check_stop_loss_positive',
        'signal_generation',
        'stop_loss > 0'
    )
    op.create_check_constraint(
        'check_take_profit_positive',
        'signal_generation',
        'take_profit > 0'
    )

def downgrade():
    # Drop constraints
    op.drop_constraint('check_contract_size_positive', 'signal_generation')
    op.drop_constraint('check_quantity_positive', 'signal_generation')
    op.drop_constraint('check_entry_price_positive', 'signal_generation')
    op.drop_constraint('check_stop_loss_positive', 'signal_generation')
    op.drop_constraint('check_take_profit_positive', 'signal_generation')

    # Drop indexes
    op.drop_index(op.f('ix_signal_generation_strategy_id'), table_name='signal_generation')
    op.drop_index(op.f('ix_signal_generation_user_id'), table_name='signal_generation')
    op.drop_index(op.f('ix_signal_generation_id'), table_name='signal_generation')

    # Drop table
    op.drop_table('signal_generation')

    # Drop enum types
    op.execute('DROP TYPE signalstatus')
    op.execute('DROP TYPE orderside')
    op.execute('DROP TYPE exchangetype')
    op.execute('DROP TYPE ordertype')
    op.execute('DROP TYPE producttype') 