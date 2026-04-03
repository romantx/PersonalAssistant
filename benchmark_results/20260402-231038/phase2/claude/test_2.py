# tests.py
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_create_wishlist():
    headers = {"Authorization": "Bearer user1"}
    response = client.post("/wishlist", headers=headers)
    assert response.status_code == 201
    assert response.json() == {"id": "user1", "items": []}

def test_view_wishlist():
    headers = {"Authorization": "Bearer user1"}
    client.post("/wishlist", headers=headers)
    response = client.get("/wishlist", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"id": "user1", "items": []}

def test_add_product():
    headers = {"Authorization": "Bearer user1"}
    client.post("/wishlist", headers=headers)
    response = client.post("/wishlist/user1/items?product_id=product1", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Product added to wishlist"}

def test_remove_product():
    headers = {"Authorization": "Bearer user1"}
    client.post("/wishlist", headers=headers)
    client.post("/wishlist/user1/items?product_id=product1", headers=headers)
    response = client.delete("/wishlist/user1/items/product1", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Product removed from wishlist"}