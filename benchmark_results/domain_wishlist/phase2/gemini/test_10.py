import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.security import create_access_token

# Use a separate in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create a fixture to set up and tear down the database for each test
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

client = TestClient(app)

# Helper to get auth headers
def get_auth_headers(user_id: str):
    token = create_access_token(data={"sub": user_id})
    return {"Authorization": f"Bearer {token}"}


def test_create_wishlist(db_session):
    headers = get_auth_headers("user1")
    response = client.post("/wishlist", headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "user1"
    assert "id" in data
    assert data["items"] == []

def test_create_wishlist_conflict(db_session):
    headers = get_auth_headers("user1")
    client.post("/wishlist", headers=headers) # First one is OK
    response = client.post("/wishlist", headers=headers) # Second one is a conflict
    assert response.status_code == 409
    assert response.json()["detail"] == "Wishlist already exists for this user"

def test_get_own_wishlist(db_session):
    headers = get_auth_headers("user2")
    # Create the wishlist first
    create_response = client.post("/wishlist", headers=headers)
    assert create_response.status_code == 201

    # Now get it
    response = client.get("/wishlist", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user2"

def test_get_wishlist_not_found(db_session):
    headers = get_auth_headers("user-no-wishlist")
    response = client.get("/wishlist", headers=headers)
    assert response.status_code == 404

def test_add_item_to_wishlist(db_session):
    headers = get_auth_headers("user3")
    create_response = client.post("/wishlist", headers=headers)
    wishlist_id = create_response.json()["id"]

    response = client.post(
        f"/wishlist/{wishlist_id}/items",
        headers=headers,
        json={"product_id": "prod123"}
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Added"

    # Verify item was added
    get_response = client.get("/wishlist", headers=headers)
    items = get_response.json()["items"]
    assert len(items) == 1
    assert items[0]["product_id"] == "prod123"

def test_add_item_to_other_users_wishlist(db_session):
    # Create wishlist for user4
    headers_user4 = get_auth_headers("user4")
    create_response = client.post("/wishlist", headers=headers_user4)
    wishlist_id = create_response.json()["id"]
    
    # Try to add item as user5
    headers_user5 = get_auth_headers("user5")
    response = client.post(
        f"/wishlist/{wishlist_id}/items",
        headers=headers_user5,
        json={"product_id": "prod123"}
    )
    assert response.status_code == 403

def test_remove_item_from_wishlist(db_session):
    headers = get_auth_headers("user6")
    create_response = client.post("/wishlist", headers=headers)
    wishlist_id = create_response.json()["id"]

    # Add an item
    client.post(
        f"/wishlist/{wishlist_id}/items",
        headers=headers,
        json={"product_id": "prod-to-remove"}
    )
    
    # Remove it
    delete_response = client.delete(
        f"/wishlist/{wishlist_id}/items/prod-to-remove",
        headers=headers
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["description"] == "Removed"

    # Verify it's gone
    get_response = client.get("/wishlist", headers=headers)
    items = get_response.json()["items"]
    assert len(items) == 0

def test_remove_nonexistent_item(db_session):
    headers = get_auth_headers("user7")
    create_response = client.post("/wishlist", headers=headers)
    wishlist_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/wishlist/{wishlist_id}/items/prod-does-not-exist",
        headers=headers
    )
    assert delete_response.status_code == 404