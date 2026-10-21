"""Esquema inicial. Não importa modelos mutáveis para preservar a migração."""
from alembic import op
import sqlalchemy as sa
revision = '001'
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    op.create_table('products', sa.Column('id',sa.Integer,primary_key=True),
        sa.Column('code',sa.String(40),nullable=False,unique=True),sa.Column('name',sa.String(120),nullable=False),
        sa.Column('category',sa.String(80),nullable=False),sa.Column('price_cents',sa.Integer,nullable=False),
        sa.Column('minimum_stock',sa.Integer,nullable=False),sa.Column('active',sa.Boolean,nullable=False),
        sa.CheckConstraint('price_cents >= 0'),sa.CheckConstraint('minimum_stock >= 0'))
    op.create_table('sales',sa.Column('id',sa.Integer,primary_key=True),sa.Column('occurred_at',sa.String(32),nullable=False),
        sa.Column('total_cents',sa.Integer,nullable=False),sa.Column('canceled_at',sa.String(32)),sa.CheckConstraint('total_cents >= 0'))
    op.create_table('sale_items',sa.Column('id',sa.Integer,primary_key=True),sa.Column('sale_id',sa.Integer,sa.ForeignKey('sales.id'),nullable=False),
        sa.Column('product_id',sa.Integer,sa.ForeignKey('products.id'),nullable=False),sa.Column('product_name',sa.String(120),nullable=False),
        sa.Column('category',sa.String(80),nullable=False),sa.Column('quantity',sa.Integer,nullable=False),sa.Column('unit_price_cents',sa.Integer,nullable=False),
        sa.Column('subtotal_cents',sa.Integer,nullable=False),sa.CheckConstraint('quantity > 0'),sa.CheckConstraint('unit_price_cents >= 0'),
        sa.CheckConstraint('subtotal_cents = quantity * unit_price_cents'),sa.UniqueConstraint('sale_id','product_id'))
    op.create_index('ix_sale_items_sale_id','sale_items',['sale_id'])
    op.create_table('movements',sa.Column('id',sa.Integer,primary_key=True),sa.Column('product_id',sa.Integer,sa.ForeignKey('products.id'),nullable=False),
        sa.Column('sale_id',sa.Integer,sa.ForeignKey('sales.id')),sa.Column('quantity',sa.Integer,nullable=False),sa.Column('kind',sa.String(20),nullable=False),
        sa.Column('reason',sa.String(240),nullable=False),sa.Column('occurred_at',sa.String(32),nullable=False),
        sa.CheckConstraint('quantity != 0'),sa.UniqueConstraint('sale_id','product_id','kind'))
    op.create_index('ix_movements_product_id','movements',['product_id'])
    op.create_index('ix_movements_sale_id','movements',['sale_id'])
def downgrade():
    raise RuntimeError('Downgrade destrutivo não é suportado nesta demonstração. Preserve um backup.')
