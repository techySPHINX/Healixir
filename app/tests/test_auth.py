from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "secure123",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    data = response.json()
    assert "token" in data
    assert data["email"] == "test@example.com"

def test_login_user():
    response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "secure123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["email"] == "test@example.com"

def test_get_current_user():
    # First, login to get the token
    login_response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "secure123"
    })
    token = login_response.json()["token"]

    # Then, use the token to fetch user info
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
