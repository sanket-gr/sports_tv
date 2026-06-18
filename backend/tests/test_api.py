import pytest
import os
test_db_path = "./test_sports_tv.db"
if os.path.exists(test_db_path):
    os.remove(test_db_path)
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

from fastapi.testclient import TestClient
from database import create_tables
from main import app

# Create tables for tests
create_tables()

def test_read_admin():
    # If no credentials are set in environment, /admin should be accessible
    if "ADMIN_USERNAME" in os.environ:
        del os.environ["ADMIN_USERNAME"]
    if "ADMIN_PASSWORD" in os.environ:
        del os.environ["ADMIN_PASSWORD"]
        
    with TestClient(app) as client:
        response = client.get("/admin")
        assert response.status_code == 200

def test_admin_auth():
    # Enable authentication
    os.environ["ADMIN_USERNAME"] = "testuser"
    os.environ["ADMIN_PASSWORD"] = "testpass"
    
    try:
        with TestClient(app) as client:
            # Unauthenticated request -> should fail with 401
            response = client.get("/admin")
            assert response.status_code == 401
            
            # Correct credentials -> should succeed with 200
            response = client.get("/admin", auth=("testuser", "testpass"))
            assert response.status_code == 200
            
            # Incorrect credentials -> should fail with 401
            response = client.get("/admin", auth=("testuser", "wrongpass"))
            assert response.status_code == 401
    finally:
        # Cleanup
        del os.environ["ADMIN_USERNAME"]
        del os.environ["ADMIN_PASSWORD"]

def test_api_categories():
    with TestClient(app) as client:
        response = client.get("/api/categories")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

def test_proxy_ssrf_mitigation():
    with TestClient(app) as client:
        # 1. Private IP block (RFC 1918, loopback)
        response = client.get("/api/proxy?url=http://127.0.0.1:8000/admin")
        assert response.status_code == 403
        assert "Private IP" in response.text
        
        response = client.get("/api/proxy?url=http://192.168.1.50/stream.m3u8")
        assert response.status_code == 403
        assert "Private IP" in response.text

        # 2. Unwhitelisted domain block
        response = client.get("/api/proxy?url=https://untrusteddomain.com/stream.m3u8")
        assert response.status_code == 403
        assert "whitelisted" in response.text

        # 3. Whitelisted domain (should pass SSRF check, even if it fails with 502/etc. from actual connection)
        response = client.get("/api/proxy?url=https://sportsurge.ws/manifest.m3u8")
        assert response.status_code in (200, 502)

