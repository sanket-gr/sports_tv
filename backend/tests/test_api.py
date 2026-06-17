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
    with TestClient(app) as client:
        response = client.get("/admin")
        assert response.status_code == 200

def test_api_categories():
    with TestClient(app) as client:
        response = client.get("/api/categories")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
