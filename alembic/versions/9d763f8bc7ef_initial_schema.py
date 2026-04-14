# """initial_schema

# Revision ID: 9d763f8bc7ef
# Revises: 
# Create Date: 2025-01-01 00:00:00.000000

# """
# from typing import Sequence, Union

# from alembic import op
# import sqlalchemy as sa
# from sqlalchemy.dialects import postgresql

# # revision identifiers, used by Alembic.
# revision: str = '9d763f8bc7ef'
# down_revision: Union[str, None] = None
# branch_labels: Union[str, Sequence[str], None] = None
# depends_on: Union[str, Sequence[str], None] = None


# def upgrade() -> None:
#     # ### Enums ###
#     userrole_enum = postgresql.ENUM('customer', 'owner', name='userrole', create_type=False)
#     userrole_enum.create(op.get_bind(), checkfirst=True)

#     orderstatus_enum = postgresql.ENUM(
#         'PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'COMPLETED', 'CANCELLED',
#         name='orderstatus', create_type=False
#     )
#     orderstatus_enum.create(op.get_bind(), checkfirst=True)

#     # ### users ###
#     op.create_table(
#         'users',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('email', sa.String(length=254), nullable=False),
#         sa.Column('hashed_password', sa.String(length=255), nullable=False),
#         sa.Column('role', sa.Enum('customer', 'owner', name='userrole'), nullable=False),
#         sa.Column('is_active', sa.Boolean(), nullable=False),
#         sa.Column('reset_token_hash', sa.String(length=64), nullable=True),
#         sa.Column('reset_token_expires_at', sa.DateTime(timezone=True), nullable=True),
#         sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.PrimaryKeyConstraint('id'),
#     )
#     op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

#     # ### customer_profiles ###
#     op.create_table(
#         'customer_profiles',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('full_name', sa.String(length=200), nullable=True),
#         sa.Column('phone', sa.String(length=20), nullable=True),
#         sa.Column('favourite_cuisine', sa.String(length=200), nullable=True),
#         sa.Column('dietary_restrictions', sa.String(length=500), nullable=True),
#         sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
#         sa.PrimaryKeyConstraint('id'),
#         sa.UniqueConstraint('user_id'),
#     )
#     op.create_index(op.f('ix_customer_profiles_user_id'), 'customer_profiles', ['user_id'], unique=False)

#     # ### owner_profiles ###
#     op.create_table(
#         'owner_profiles',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('full_name', sa.String(length=200), nullable=True),
#         sa.Column('phone', sa.String(length=20), nullable=True),
#         sa.Column('bio', sa.String(length=1000), nullable=True),
#         sa.Column('favourite_cuisine', sa.String(length=200), nullable=True),
#         sa.Column('dietary_restrictions', sa.String(length=500), nullable=True),
#         sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
#         sa.PrimaryKeyConstraint('id'),
#         sa.UniqueConstraint('user_id'),
#     )
#     op.create_index(op.f('ix_owner_profiles_user_id'), 'owner_profiles', ['user_id'], unique=False)

#     # ### restaurants ###
#     op.create_table(
#         'restaurants',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('name', sa.String(length=200), nullable=False),
#         sa.Column('cuisine_type', sa.String(length=100), nullable=True),
#         sa.Column('location', sa.String(length=300), nullable=True),
#         sa.Column('description', sa.Text(), nullable=True),
#         sa.Column('image_url', sa.Text(), nullable=True),
#         sa.Column('is_active', sa.Boolean(), nullable=False),
#         sa.Column('rating', sa.Numeric(precision=3, scale=2), nullable=True),
#         sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
#         sa.PrimaryKeyConstraint('id'),
#     )
#     op.create_index(op.f('ix_restaurants_name'), 'restaurants', ['name'], unique=False)
#     op.create_index(op.f('ix_restaurants_owner_id'), 'restaurants', ['owner_id'], unique=False)

#     # ### favourite_restaurants ###
#     op.create_table(
#         'favourite_restaurants',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.ForeignKeyConstraint(['customer_id'], ['customer_profiles.id'], ondelete='CASCADE'),
#         sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
#         sa.PrimaryKeyConstraint('id'),
#         sa.UniqueConstraint('customer_id', 'restaurant_id', name='uq_fav_customer_restaurant'),
#     )
#     op.create_index(op.f('ix_favourite_restaurants_customer_id'), 'favourite_restaurants', ['customer_id'], unique=False)
#     op.create_index(op.f('ix_favourite_restaurants_restaurant_id'), 'favourite_restaurants', ['restaurant_id'], unique=False)

#     # ### menu_items ###
#     op.create_table(
#         'menu_items',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('name', sa.String(length=200), nullable=False),
#         sa.Column('description', sa.Text(), nullable=True),
#         sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
#         sa.Column('category', sa.String(length=100), nullable=True),
#         sa.Column('image_url', sa.Text(), nullable=True),
#         sa.Column('is_available', sa.Boolean(), nullable=False),
#         sa.Column('is_special', sa.Boolean(), nullable=False),
#         sa.Column('order_count', sa.Integer(), nullable=False),
#         sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
#         sa.PrimaryKeyConstraint('id'),
#     )
#     op.create_index(op.f('ix_menu_items_category'), 'menu_items', ['category'], unique=False)
#     op.create_index(op.f('ix_menu_items_restaurant_id'), 'menu_items', ['restaurant_id'], unique=False)

#     # ### orders ###
#     op.create_table(
#         'orders',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('status', sa.Enum('PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'COMPLETED', 'CANCELLED', name='orderstatus'), nullable=False),
#         sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
#         sa.Column('special_instructions', sa.Text(), nullable=True),
#         sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.ForeignKeyConstraint(['customer_id'], ['customer_profiles.id'], ondelete='RESTRICT'),
#         sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='RESTRICT'),
#         sa.PrimaryKeyConstraint('id'),
#     )
#     op.create_index(op.f('ix_orders_customer_id'), 'orders', ['customer_id'], unique=False)
#     op.create_index(op.f('ix_orders_restaurant_id'), 'orders', ['restaurant_id'], unique=False)
#     op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)

#     # ### order_items ###
#     op.create_table(
#         'order_items',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('quantity', sa.Integer(), nullable=False),
#         sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
#         sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
#         sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='RESTRICT'),
#         sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
#         sa.PrimaryKeyConstraint('id'),
#     )
#     op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)

#     # ### cart_items ###
#     op.create_table(
#         'cart_items',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('quantity', sa.Integer(), nullable=False),
#         sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.ForeignKeyConstraint(['customer_id'], ['customer_profiles.id'], ondelete='CASCADE'),
#         sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='CASCADE'),
#         sa.PrimaryKeyConstraint('id'),
#         sa.UniqueConstraint('customer_id', 'menu_item_id', name='uq_cart_customer_item'),
#     )
#     op.create_index(op.f('ix_cart_items_customer_id'), 'cart_items', ['customer_id'], unique=False)

#     # ### refresh_tokens ###
#     op.create_table(
#         'refresh_tokens',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('token_hash', sa.String(length=64), nullable=False),
#         sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
#         sa.Column('revoked', sa.Boolean(), nullable=False),
#         sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
#         sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
#         sa.PrimaryKeyConstraint('id'),
#         sa.UniqueConstraint('token_hash'),
#     )
#     op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)


# def downgrade() -> None:
#     op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
#     op.drop_table('refresh_tokens')

#     op.drop_index(op.f('ix_cart_items_customer_id'), table_name='cart_items')
#     op.drop_table('cart_items')

#     op.drop_index(op.f('ix_order_items_order_id'), table_name='order_items')
#     op.drop_table('order_items')

#     op.drop_index(op.f('ix_orders_status'), table_name='orders')
#     op.drop_index(op.f('ix_orders_restaurant_id'), table_name='orders')
#     op.drop_index(op.f('ix_orders_customer_id'), table_name='orders')
#     op.drop_table('orders')

#     op.drop_index(op.f('ix_menu_items_restaurant_id'), table_name='menu_items')
#     op.drop_index(op.f('ix_menu_items_category'), table_name='menu_items')
#     op.drop_table('menu_items')

#     op.drop_index(op.f('ix_favourite_restaurants_restaurant_id'), table_name='favourite_restaurants')
#     op.drop_index(op.f('ix_favourite_restaurants_customer_id'), table_name='favourite_restaurants')
#     op.drop_table('favourite_restaurants')

#     op.drop_index(op.f('ix_restaurants_owner_id'), table_name='restaurants')
#     op.drop_index(op.f('ix_restaurants_name'), table_name='restaurants')
#     op.drop_table('restaurants')

#     op.drop_index(op.f('ix_owner_profiles_user_id'), table_name='owner_profiles')
#     op.drop_table('owner_profiles')

#     op.drop_index(op.f('ix_customer_profiles_user_id'), table_name='customer_profiles')
#     op.drop_table('customer_profiles')

#     op.drop_index(op.f('ix_users_email'), table_name='users')
#     op.drop_table('users')

#     sa.Enum(name='orderstatus').drop(op.get_bind(), checkfirst=True)
#     sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)


"""initial_schema

Revision ID: 9d763f8bc7ef
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '9d763f8bc7ef'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    userrole_enum = postgresql.ENUM('customer', 'owner', name='userrole', create_type=False)
    userrole_enum.create(bind, checkfirst=True)

    orderstatus_enum = postgresql.ENUM(
        'PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'COMPLETED', 'CANCELLED',
        name='orderstatus',
        create_type=False,
    )
    orderstatus_enum.create(bind, checkfirst=True)

    # 1. users — root table, no FK dependencies
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', userrole_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('reset_token_hash', sa.String(length=64), nullable=True),
        sa.Column('reset_token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. refresh_tokens — FK → users
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)

    # 3. customer_profiles — FK → users
    op.create_table(
        'customer_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('favourite_cuisine', sa.String(length=200), nullable=True),
        sa.Column('dietary_restrictions', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_customer_profiles_user_id'), 'customer_profiles', ['user_id'], unique=False)

    # 4. owner_profiles — FK → users
    op.create_table(
        'owner_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('bio', sa.String(length=1000), nullable=True),
        sa.Column('favourite_cuisine', sa.String(length=200), nullable=True),
        sa.Column('dietary_restrictions', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_owner_profiles_user_id'), 'owner_profiles', ['user_id'], unique=False)

    # 5. restaurants — FK → users
    op.create_table(
        'restaurants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('cuisine_type', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=300), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('rating', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_restaurants_name'), 'restaurants', ['name'], unique=False)
    op.create_index(op.f('ix_restaurants_owner_id'), 'restaurants', ['owner_id'], unique=False)

    # 6. favourite_restaurants — FK → customer_profiles, restaurants
    op.create_table(
        'favourite_restaurants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id', 'restaurant_id', name='uq_fav_customer_restaurant'),
    )
    op.create_index(op.f('ix_favourite_restaurants_customer_id'), 'favourite_restaurants', ['customer_id'], unique=False)
    op.create_index(op.f('ix_favourite_restaurants_restaurant_id'), 'favourite_restaurants', ['restaurant_id'], unique=False)

    # 7. menu_items — FK → restaurants
    op.create_table(
        'menu_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=False),
        sa.Column('is_special', sa.Boolean(), nullable=False),
        sa.Column('order_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_menu_items_category'), 'menu_items', ['category'], unique=False)
    op.create_index(op.f('ix_menu_items_restaurant_id'), 'menu_items', ['restaurant_id'], unique=False)

    # 8. orders — FK → customer_profiles, restaurants
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', orderstatus_enum, nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('special_instructions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customer_profiles.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_orders_customer_id'), 'orders', ['customer_id'], unique=False)
    op.create_index(op.f('ix_orders_restaurant_id'), 'orders', ['restaurant_id'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)

    # 9. order_items — FK → orders, menu_items
    op.create_table(
        'order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)

    # 10. cart_items — FK → customer_profiles, menu_items
    op.create_table(
        'cart_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customer_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id', 'menu_item_id', name='uq_cart_customer_item'),
    )
    op.create_index(op.f('ix_cart_items_customer_id'), 'cart_items', ['customer_id'], unique=False)


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index(op.f('ix_cart_items_customer_id'), table_name='cart_items')
    op.drop_table('cart_items')

    op.drop_index(op.f('ix_order_items_order_id'), table_name='order_items')
    op.drop_table('order_items')

    op.drop_index(op.f('ix_orders_status'), table_name='orders')
    op.drop_index(op.f('ix_orders_restaurant_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_customer_id'), table_name='orders')
    op.drop_table('orders')

    op.drop_index(op.f('ix_menu_items_restaurant_id'), table_name='menu_items')
    op.drop_index(op.f('ix_menu_items_category'), table_name='menu_items')
    op.drop_table('menu_items')

    op.drop_index(op.f('ix_favourite_restaurants_restaurant_id'), table_name='favourite_restaurants')
    op.drop_index(op.f('ix_favourite_restaurants_customer_id'), table_name='favourite_restaurants')
    op.drop_table('favourite_restaurants')

    op.drop_index(op.f('ix_restaurants_owner_id'), table_name='restaurants')
    op.drop_index(op.f('ix_restaurants_name'), table_name='restaurants')
    op.drop_table('restaurants')

    op.drop_index(op.f('ix_owner_profiles_user_id'), table_name='owner_profiles')
    op.drop_table('owner_profiles')

    op.drop_index(op.f('ix_customer_profiles_user_id'), table_name='customer_profiles')
    op.drop_table('customer_profiles')

    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    sa.Enum(name='orderstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)