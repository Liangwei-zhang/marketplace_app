"""
API Tests for Marketplace App
"""
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from app.main import app
from app.core.database import async_engine, async_session_maker


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def clean_db():
    """Clean database before each test"""
    async with async_engine.begin() as conn:
        await conn.execute(text("DELETE FROM messages"))
        await conn.execute(text("DELETE FROM chat_rooms"))
        await conn.execute(text("DELETE FROM transactions"))
        await conn.execute(text("DELETE FROM items"))
        await conn.execute(text("DELETE FROM users"))
        await conn.commit()
    yield
    async with async_engine.begin() as conn:
        await conn.execute(text("DELETE FROM messages"))
        await conn.execute(text("DELETE FROM chat_rooms"))
        await conn.execute(text("DELETE FROM transactions"))
        await conn.execute(text("DELETE FROM items"))
        await conn.execute(text("DELETE FROM users"))
        await conn.commit()


# Helper to get auth token
async def register_and_login(client: AsyncClient, username="testuser", password="testpass123"):
    # Register
    resp = await client.post("/api/v1/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": password,
        "full_name": "Test User"
    })
    assert resp.status_code == 201
    
    # Login
    resp = await client.post("/api/v1/auth/login", data={
        "username": username,
        "password": password
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


class TestAuth:
    async def test_register(self, client, clean_db):
        resp = await client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "password123",
            "full_name": "New User"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@test.com"
    
    async def test_register_duplicate_username(self, client, clean_db):
        await register_and_login(client, "user1", "pass123")
        
        resp = await client.post("/api/v1/auth/register", json={
            "username": "user1",
            "email": "another@test.com",
            "password": "pass123"
        })
        assert resp.status_code == 400
    
    async def test_login(self, client, clean_db):
        await register_and_login(client, "loginuser", "mypassword")
        
        resp = await client.post("/api/v1/auth/login", data={
            "username": "loginuser",
            "password": "mypassword"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()
    
    async def test_login_wrong_password(self, client, clean_db):
        await register_and_login(client, "user2", "correctpass")
        
        resp = await client.post("/api/v1/auth/login", data={
            "username": "user2",
            "password": "wrongpass"
        })
        assert resp.status_code == 401
    
    async def test_get_me(self, client, clean_db):
        token = await register_and_login(client, "meuser", "pass123")
        
        resp = await client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 200
        assert resp.json()["username"] == "meuser"


class TestCategories:
    async def test_list_categories(self, client):
        resp = await client.get("/api/v1/items/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        assert "electronics" in data["categories"]
        assert "clothing" in data["categories"]
        assert len(data["categories"]) == 7


class TestItems:
    async def test_create_item(self, client, clean_db):
        token = await register_and_login(client)
        
        resp = await client.post("/api/v1/items/", 
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Test Item",
                "description": "A test item description",
                "price": 99.99,
                "category": "electronics",
                "latitude": 51.0447,
                "longitude": -114.0719,
                "address": "Calgary, AB"
            }
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test Item"
        assert data["price"] == 99.99
        assert data["category"] == "electronics"
    
    async def test_create_item_invalid_category(self, client, clean_db):
        token = await register_and_login(client)
        
        resp = await client.post("/api/v1/items/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Test",
                "description": "Test",
                "price": 10,
                "category": "invalid_category",
                "latitude": 51.0,
                "longitude": -114.0
            }
        )
        assert resp.status_code == 422
    
    async def test_list_items(self, client, clean_db):
        token = await register_and_login(client)
        
        # Create an item
        await client.post("/api/v1/items/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "List Item",
                "description": "Desc",
                "price": 50,
                "category": "books",
                "latitude": 51.0,
                "longitude": -114.0
            }
        )
        
        # List items
        resp = await client.get("/api/v1/items/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
    
    async def test_search_items(self, client, clean_db):
        token = await register_and_login(client)
        
        # Create item in Calgary
        await client.post("/api/v1/items/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Calgary Item",
                "description": "In Calgary",
                "price": 100,
                "category": "electronics",
                "latitude": 51.0447,
                "longitude": -114.0719
            }
        )
        
        # Search nearby
        resp = await client.post("/api/v1/items/search", json={
            "latitude": 51.0447,
            "longitude": -114.0719,
            "radius_km": 10
        })
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
    
    async def test_search_with_category_filter(self, client, clean_db):
        token = await register_and_login(client)
        
        # Create items
        await client.post("/api/v1/items/",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Elec1", "description": "E", "price": 10, "category": "electronics", "latitude": 51.0, "longitude": -114.0}
        )
        await client.post("/api/v1/items/",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Furn1", "description": "F", "price": 20, "category": "furniture", "latitude": 51.0, "longitude": -114.0}
        )
        
        # Filter by electronics
        resp = await client.post("/api/v1/items/search", json={
            "latitude": 51.0,
            "longitude": -114.0,
            "radius_km": 10,
            "category": "electronics"
        })
        assert resp.status_code == 200
        items = resp.json()
        assert all(item["category"] == "electronics" for item in items)
    
    async def test_get_item(self, client, clean_db):
        token = await register_and_login(client)
        
        # Create item
        create_resp = await client.post("/api/v1/items/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Get Test",
                "description": "Testing get",
                "price": 25,
                "category": "games",
                "latitude": 51.0,
                "longitude": -114.0
            }
        )
        item_id = create_resp.json()["id"]
        
        # Get item
        resp = await client.get(f"/api/v1/items/{item_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Get Test"
    
    async def test_update_item(self, client, clean_db):
        token = await register_and_login(client)
        
        # Create item
        create_resp = await client.post("/api/v1/items/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Original",
                "description": "Desc",
                "price": 10,
                "category": "other",
                "latitude": 51.0,
                "longitude": -114.0
            }
        )
        item_id = create_resp.json()["id"]
        
        # Update
        resp = await client.put(f"/api/v1/items/{item_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Updated", "price": 15}
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"
        assert resp.json()["price"] == 15
    
    async def test_delete_item(self, client, clean_db):
        token = await register_and_login(client)
        
        # Create item
        create_resp = await client.post("/api/v1/items/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "To Delete",
                "description": "Desc",
                "price": 10,
                "category": "other",
                "latitude": 51.0,
                "longitude": -114.0
            }
        )
        item_id = create_resp.json()["id"]
        
        # Delete
        resp = await client.delete(f"/api/v1/items/{item_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 204
        
        # Verify deleted
        resp = await client.get(f"/api/v1/items/{item_id}")
        assert resp.status_code == 404


class TestTransactions:
    async def test_create_transaction(self, client, clean_db):
        # Seller
        token1 = await register_and_login(client, "seller1", "pass123")
        
        # Create item
        item_resp = await client.post("/api/v1/items/",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "title": "Item for Sale",
                "description": "Test",
                "price": 100,
                "category": "electronics",
                "latitude": 51.0,
                "longitude": -114.0
            }
        )
        item_id = item_resp.json()["id"]
        
        # Buyer (need different client to maintain auth)
        async with AsyncClient(base_url="http://test") as buyer_client:
            token2 = await register_and_login(buyer_client, "buyer1", "pass123")
            
            # Create transaction
            resp = await buyer_client.post("/api/v1/transactions/",
                headers={"Authorization": f"Bearer {token2}"},
                json={
                    "item_id": item_id,
                    "agreed_price": 90,
                    "note": "I'll take it"
                }
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["agreed_price"] == 90
            assert data["status"] == "pending"
    
    async def test_cannot_buy_own_item(self, client, clean_db):
        token = await register_and_login(client)
        
        # Create item
        item_resp = await client.post("/api/v1/items/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "My Item",
                "description": "Test",
                "price": 50,
                "category": "other",
                "latitude": 51.0,
                "longitude": -114.0
            }
        )
        item_id = item_resp.json()["id"]
        
        # Try to buy own item
        resp = await client.post("/api/v1/transactions/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "item_id": item_id,
                "agreed_price": 50
            }
        )
        assert resp.status_code == 400


class TestHealth:
    async def test_health_check(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestNotFound:
    async def test_404(self, client):
        resp = await client.get("/api/v1/items/99999")
        assert resp.status_code == 404
