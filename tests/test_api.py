"""
Pytest test suite for the JustEats API.

Covers (≥ 10 tests):
  1.  register – success
  2.  register – duplicate email → 409
  3.  register – weak password → 422
  4.  login – success, tokens returned
  5.  login – wrong password → 401
  6.  JWT expiry – expired token → 401
  7.  CRUD restaurants – create / list / update / delete
  8.  Place order – happy path, total calculated correctly
  9.  Update order status – PENDING → CONFIRMED
  10. Customer profile – get & patch
  11. Favourites – add & list
  12. Recommendations – returns list

Run with:
    cd backend
    venv\\Scripts\\pytest          (Windows)
    source venv/bin/activate && pytest   (Unix)

Requires a reachable PostgreSQL instance at TEST_DATABASE_URL
(default: postgresql+asyncpg://postgres:postgres@localhost:5432/justeats_test).
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import settings

PREFIX = "/api/v1"


# ─── Tiny helpers ─────────────────────────────────────────────────────────────


async def _register(client: AsyncClient, email: str, password: str, role: str = "customer"):
    return await client.post(
        f"{PREFIX}/auth/register",
        json={"email": email, "password": password, "role": role},
    )


async def _login(client: AsyncClient, email: str, password: str):
    return await client.post(
        f"{PREFIX}/auth/login",
        json={"email": email, "password": password},
    )


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _owner_token(client: AsyncClient, email: str = "owner@example.com") -> str:
    await _register(client, email, "Password123!", role="owner")
    r = await _login(client, email, "Password123!")
    return r.json()["access_token"]


async def _customer_token(client: AsyncClient, email: str = "cust@example.com") -> str:
    await _register(client, email, "Password123!")
    r = await _login(client, email, "Password123!")
    return r.json()["access_token"]


async def _ensure_profile(client: AsyncClient, token: str):
    """GET /profile creates the profile record automatically."""
    await client.get(f"{PREFIX}/profile", headers=_auth(token))


async def _create_restaurant(client: AsyncClient, token: str, name: str = "Test Bistro") -> dict:
    r = await client.post(
        f"{PREFIX}/restaurants",
        json={"name": name, "cuisine_type": "Fusion", "location": "London"},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _create_menu_item(client: AsyncClient, token: str, restaurant_id: str, name: str = "Test Dish") -> dict:
    r = await client.post(
        f"{PREFIX}/restaurants/{restaurant_id}/menu-items",
        json={"name": name, "price": "9.99", "is_available": True},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


# ═══════════════════════════════════════════════════════════════════════════════
# 1 & 2 & 3 – Register
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_register_success(client):
    res = await _register(client, "new@example.com", "Secure123!")
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "new@example.com"
    assert data["role"] == "customer"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    await _register(client, "dup@example.com", "Secure123!")
    res = await _register(client, "dup@example.com", "Secure123!")
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password_returns_422(client):
    res = await _register(client, "weak@example.com", "short")
    assert res.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 4 & 5 – Login
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_login_success_returns_token_pair(client):
    await _register(client, "login@example.com", "Secure123!")
    res = await _login(client, "login@example.com", "Secure123!")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    await _register(client, "badpw@example.com", "Secure123!")
    res = await _login(client, "badpw@example.com", "wrongpassword")
    assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# 6 – JWT expiry
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_expired_jwt_returns_401(client):
    expired_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "role": "customer",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
            "type": "access",
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    res = await client.get(f"{PREFIX}/auth/me", headers=_auth(expired_token))
    assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# 7 – CRUD Restaurant
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_restaurant(client):
    token = await _owner_token(client)
    data = await _create_restaurant(client, token, "Burger Palace")
    assert data["name"] == "Burger Palace"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_restaurants_is_public(client):
    token = await _owner_token(client)
    await _create_restaurant(client, token, "Pizza Town")
    res = await client.get(f"{PREFIX}/restaurants")
    assert res.status_code == 200
    assert any(r["name"] == "Pizza Town" for r in res.json())


@pytest.mark.asyncio
async def test_update_restaurant(client):
    token = await _owner_token(client)
    restaurant = await _create_restaurant(client, token, "Old Name")
    res = await client.patch(
        f"{PREFIX}/restaurants/{restaurant['id']}",
        json={"name": "New Name", "cuisine_type": "Modern"},
        headers=_auth(token),
    )
    assert res.status_code == 200
    assert res.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_restaurant(client):
    token = await _owner_token(client)
    restaurant = await _create_restaurant(client, token, "To Be Deleted")
    res = await client.delete(
        f"{PREFIX}/restaurants/{restaurant['id']}",
        headers=_auth(token),
    )
    assert res.status_code == 204
    # Confirm it no longer appears in list
    list_res = await client.get(f"{PREFIX}/restaurants")
    ids = [r["id"] for r in list_res.json()]
    assert restaurant["id"] not in ids


@pytest.mark.asyncio
async def test_create_restaurant_forbidden_for_customer(client):
    token = await _customer_token(client)
    res = await client.post(
        f"{PREFIX}/restaurants",
        json={"name": "Not Allowed"},
        headers=_auth(token),
    )
    assert res.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# 8 – Place order
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_place_order_calculates_total(client):
    owner = await _owner_token(client, "owner2@example.com")
    cust = await _customer_token(client, "cust2@example.com")

    rest = await _create_restaurant(client, owner, "Order Test")
    item = await _create_menu_item(client, owner, rest["id"], "Test Dish")  # price 9.99

    await _ensure_profile(client, cust)

    res = await client.post(
        f"{PREFIX}/orders",
        json={
            "restaurant_id": rest["id"],
            "items": [{"menu_item_id": item["id"], "quantity": 2}],
        },
        headers=_auth(cust),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "PENDING"
    assert float(data["total_amount"]) == pytest.approx(19.98)
    assert len(data["order_items"]) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# 9 – Update order status
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_update_order_status_pending_to_confirmed(client):
    owner = await _owner_token(client, "owner3@example.com")
    cust = await _customer_token(client, "cust3@example.com")

    rest = await _create_restaurant(client, owner, "Status Test")
    item = await _create_menu_item(client, owner, rest["id"])

    await _ensure_profile(client, cust)

    order_res = await client.post(
        f"{PREFIX}/orders",
        json={"restaurant_id": rest["id"], "items": [{"menu_item_id": item["id"], "quantity": 1}]},
        headers=_auth(cust),
    )
    order_id = order_res.json()["id"]

    res = await client.patch(
        f"{PREFIX}/orders/{order_id}/status",
        json={"status": "CONFIRMED"},
        headers=_auth(owner),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_invalid_order_status_transition_returns_422(client):
    owner = await _owner_token(client, "owner4@example.com")
    cust = await _customer_token(client, "cust4@example.com")

    rest = await _create_restaurant(client, owner, "Trans Test")
    item = await _create_menu_item(client, owner, rest["id"])
    await _ensure_profile(client, cust)

    order_res = await client.post(
        f"{PREFIX}/orders",
        json={"restaurant_id": rest["id"], "items": [{"menu_item_id": item["id"], "quantity": 1}]},
        headers=_auth(cust),
    )
    order_id = order_res.json()["id"]

    # Jump directly from PENDING → COMPLETED (invalid)
    res = await client.patch(
        f"{PREFIX}/orders/{order_id}/status",
        json={"status": "COMPLETED"},
        headers=_auth(owner),
    )
    assert res.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 10 – Customer profile
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_profile_creates_if_missing(client):
    token = await _customer_token(client, "prof@example.com")
    res = await client.get(f"{PREFIX}/profile", headers=_auth(token))
    assert res.status_code == 200
    assert "id" in res.json()
    assert "user_id" in res.json()


@pytest.mark.asyncio
async def test_update_profile(client):
    token = await _customer_token(client, "profupd@example.com")
    res = await client.patch(
        f"{PREFIX}/profile",
        json={"full_name": "Alice Smith", "phone": "+447911000099", "favourite_cuisine": "Japanese"},
        headers=_auth(token),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Alice Smith"
    assert data["favourite_cuisine"] == "Japanese"


# ═══════════════════════════════════════════════════════════════════════════════
# 11 – Favourites
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_add_and_list_favourites(client):
    owner = await _owner_token(client, "owner5@example.com")
    cust = await _customer_token(client, "cust5@example.com")
    await _ensure_profile(client, cust)

    rest = await _create_restaurant(client, owner, "Fave Spot")

    add_res = await client.post(f"{PREFIX}/favourites/{rest['id']}", headers=_auth(cust))
    assert add_res.status_code == 201

    list_res = await client.get(f"{PREFIX}/favourites", headers=_auth(cust))
    assert list_res.status_code == 200
    assert any(r["id"] == rest["id"] for r in list_res.json())


@pytest.mark.asyncio
async def test_add_favourite_twice_returns_409(client):
    owner = await _owner_token(client, "owner6@example.com")
    cust = await _customer_token(client, "cust6@example.com")
    await _ensure_profile(client, cust)

    rest = await _create_restaurant(client, owner, "Double Fave")

    await client.post(f"{PREFIX}/favourites/{rest['id']}", headers=_auth(cust))
    res = await client.post(f"{PREFIX}/favourites/{rest['id']}", headers=_auth(cust))
    assert res.status_code == 409


# ═══════════════════════════════════════════════════════════════════════════════
# 12 – Recommendations
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_recommendations_returns_list(client):
    """Without any completed orders, recommendations fall back to top-rated restaurants."""
    token = await _customer_token(client, "rec@example.com")
    await _ensure_profile(client, token)

    res = await client.get(f"{PREFIX}/recommendations", headers=_auth(token))
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ═══════════════════════════════════════════════════════════════════════════════
# 13 – auth/me endpoint
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_me_returns_authenticated_user(client):
    await _register(client, "me@example.com", "Secure123!", role="customer")
    r = await _login(client, "me@example.com", "Secure123!")
    token = r.json()["access_token"]

    res = await client.get(f"{PREFIX}/auth/me", headers=_auth(token))
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "me@example.com"
    assert data["role"] == "customer"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client):
    res = await client.get(f"{PREFIX}/auth/me")
    assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# 14 – Token refresh & logout
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_refresh_token_issues_new_pair(client):
    await _register(client, "ref@example.com", "Secure123!")
    login_res = await _login(client, "ref@example.com", "Secure123!")
    refresh_token = login_res.json()["refresh_token"]

    res = await client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # Old refresh token should be revoked – using it again must fail
    res2 = await client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": refresh_token})
    assert res2.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client):
    await _register(client, "logout@example.com", "Secure123!")
    login_res = await _login(client, "logout@example.com", "Secure123!")
    refresh_token = login_res.json()["refresh_token"]

    logout_res = await client.post(f"{PREFIX}/auth/logout", json={"refresh_token": refresh_token})
    assert logout_res.status_code == 204

    # Using the revoked token should now fail
    refresh_res = await client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# 15 – Menu item CRUD
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_menu_items_is_public(client):
    owner = await _owner_token(client, "menu_owner1@example.com")
    rest = await _create_restaurant(client, owner, "Menu List Test")
    await _create_menu_item(client, owner, rest["id"], "Pasta")
    await _create_menu_item(client, owner, rest["id"], "Risotto")

    res = await client.get(f"{PREFIX}/restaurants/{rest['id']}/menu-items")
    assert res.status_code == 200
    names = [i["name"] for i in res.json()]
    assert "Pasta" in names
    assert "Risotto" in names


@pytest.mark.asyncio
async def test_get_single_menu_item(client):
    owner = await _owner_token(client, "menu_owner2@example.com")
    rest = await _create_restaurant(client, owner, "Single Item Test")
    item = await _create_menu_item(client, owner, rest["id"], "Steak")

    res = await client.get(f"{PREFIX}/restaurants/{rest['id']}/menu-items/{item['id']}")
    assert res.status_code == 200
    assert res.json()["name"] == "Steak"
    assert float(res.json()["price"]) == pytest.approx(9.99)


@pytest.mark.asyncio
async def test_update_menu_item(client):
    owner = await _owner_token(client, "menu_owner3@example.com")
    rest = await _create_restaurant(client, owner, "Update Item Test")
    item = await _create_menu_item(client, owner, rest["id"], "Old Name")

    res = await client.patch(
        f"{PREFIX}/restaurants/{rest['id']}/menu-items/{item['id']}",
        json={"name": "New Name", "price": "14.99"},
        headers=_auth(owner),
    )
    assert res.status_code == 200
    assert res.json()["name"] == "New Name"
    assert float(res.json()["price"]) == pytest.approx(14.99)


@pytest.mark.asyncio
async def test_delete_menu_item(client):
    owner = await _owner_token(client, "menu_owner4@example.com")
    rest = await _create_restaurant(client, owner, "Delete Item Test")
    item = await _create_menu_item(client, owner, rest["id"], "To Delete")

    del_res = await client.delete(
        f"{PREFIX}/restaurants/{rest['id']}/menu-items/{item['id']}",
        headers=_auth(owner),
    )
    assert del_res.status_code == 204

    get_res = await client.get(f"{PREFIX}/restaurants/{rest['id']}/menu-items/{item['id']}")
    assert get_res.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 16 – Cart operations
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_add_item_to_cart(client):
    owner = await _owner_token(client, "cart_owner1@example.com")
    cust = await _customer_token(client, "cart_cust1@example.com")
    await _ensure_profile(client, cust)

    rest = await _create_restaurant(client, owner, "Cart Test")
    item = await _create_menu_item(client, owner, rest["id"], "Burger")

    res = await client.post(
        f"{PREFIX}/cart",
        json={"menu_item_id": item["id"], "quantity": 2},
        headers=_auth(cust),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["menu_item_id"] == item["id"]
    assert data["quantity"] == 2
    assert float(data["subtotal"]) == pytest.approx(19.98)


@pytest.mark.asyncio
async def test_view_cart_returns_items(client):
    owner = await _owner_token(client, "cart_owner2@example.com")
    cust = await _customer_token(client, "cart_cust2@example.com")
    await _ensure_profile(client, cust)

    rest = await _create_restaurant(client, owner, "Cart View Test")
    item = await _create_menu_item(client, owner, rest["id"], "Pizza")

    await client.post(f"{PREFIX}/cart", json={"menu_item_id": item["id"], "quantity": 1}, headers=_auth(cust))

    res = await client.get(f"{PREFIX}/cart", headers=_auth(cust))
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["name"] == "Pizza"


@pytest.mark.asyncio
async def test_update_cart_item_quantity(client):
    owner = await _owner_token(client, "cart_owner3@example.com")
    cust = await _customer_token(client, "cart_cust3@example.com")
    await _ensure_profile(client, cust)

    rest = await _create_restaurant(client, owner, "Cart Update Test")
    item = await _create_menu_item(client, owner, rest["id"], "Wrap")

    add_res = await client.post(
        f"{PREFIX}/cart", json={"menu_item_id": item["id"], "quantity": 1}, headers=_auth(cust)
    )
    cart_item_id = add_res.json()["id"]

    res = await client.patch(
        f"{PREFIX}/cart/{cart_item_id}",
        json={"quantity": 5},
        headers=_auth(cust),
    )
    assert res.status_code == 200
    assert res.json()["quantity"] == 5


@pytest.mark.asyncio
async def test_remove_cart_item(client):
    owner = await _owner_token(client, "cart_owner4@example.com")
    cust = await _customer_token(client, "cart_cust4@example.com")
    await _ensure_profile(client, cust)

    rest = await _create_restaurant(client, owner, "Cart Remove Test")
    item = await _create_menu_item(client, owner, rest["id"], "Salad")

    add_res = await client.post(
        f"{PREFIX}/cart", json={"menu_item_id": item["id"], "quantity": 1}, headers=_auth(cust)
    )
    cart_item_id = add_res.json()["id"]

    del_res = await client.delete(f"{PREFIX}/cart/{cart_item_id}", headers=_auth(cust))
    assert del_res.status_code == 204

    view_res = await client.get(f"{PREFIX}/cart", headers=_auth(cust))
    assert view_res.json() == []


@pytest.mark.asyncio
async def test_clear_cart(client):
    owner = await _owner_token(client, "cart_owner5@example.com")
    cust = await _customer_token(client, "cart_cust5@example.com")
    await _ensure_profile(client, cust)

    rest = await _create_restaurant(client, owner, "Cart Clear Test")
    item1 = await _create_menu_item(client, owner, rest["id"], "Item A")
    item2 = await _create_menu_item(client, owner, rest["id"], "Item B")

    await client.post(f"{PREFIX}/cart", json={"menu_item_id": item1["id"], "quantity": 1}, headers=_auth(cust))
    await client.post(f"{PREFIX}/cart", json={"menu_item_id": item2["id"], "quantity": 1}, headers=_auth(cust))

    clear_res = await client.delete(f"{PREFIX}/cart", headers=_auth(cust))
    assert clear_res.status_code == 204

    view_res = await client.get(f"{PREFIX}/cart", headers=_auth(cust))
    assert view_res.json() == []


# ═══════════════════════════════════════════════════════════════════════════════
# 17 – Order history
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_my_orders(client):
    owner = await _owner_token(client, "hist_owner@example.com")
    cust = await _customer_token(client, "hist_cust@example.com")
    await _ensure_profile(client, cust)

    rest = await _create_restaurant(client, owner, "History Test")
    item = await _create_menu_item(client, owner, rest["id"])

    await client.post(
        f"{PREFIX}/orders",
        json={"restaurant_id": rest["id"], "items": [{"menu_item_id": item["id"], "quantity": 1}]},
        headers=_auth(cust),
    )

    res = await client.get(f"{PREFIX}/orders/my", headers=_auth(cust))
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_list_restaurant_orders_by_owner(client):
    owner = await _owner_token(client, "rest_ord_owner@example.com")
    cust = await _customer_token(client, "rest_ord_cust@example.com")
    await _ensure_profile(client, cust)

    rest = await _create_restaurant(client, owner, "Owned Orders Test")
    item = await _create_menu_item(client, owner, rest["id"])

    await client.post(
        f"{PREFIX}/orders",
        json={"restaurant_id": rest["id"], "items": [{"menu_item_id": item["id"], "quantity": 1}]},
        headers=_auth(cust),
    )

    res = await client.get(f"{PREFIX}/orders/restaurant/{rest['id']}", headers=_auth(owner))
    assert res.status_code == 200
    assert len(res.json()) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# 18 – Remove favourite
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_remove_favourite(client):
    owner = await _owner_token(client, "fav_rm_owner@example.com")
    cust = await _customer_token(client, "fav_rm_cust@example.com")
    await _ensure_profile(client, cust)

    rest = await _create_restaurant(client, owner, "Remove Fave")

    await client.post(f"{PREFIX}/favourites/{rest['id']}", headers=_auth(cust))
    del_res = await client.delete(f"{PREFIX}/favourites/{rest['id']}", headers=_auth(cust))
    assert del_res.status_code == 204

    list_res = await client.get(f"{PREFIX}/favourites", headers=_auth(cust))
    assert not any(r["id"] == rest["id"] for r in list_res.json())
