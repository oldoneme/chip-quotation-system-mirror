import sys
import os

# Add the project root directory to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_root():
    response = client.get("/")
    print("Root endpoint:", response.status_code, response.json())

def test_machine_types():
    response = client.get("/api/v1/machine-types/")
    print("Machine types endpoint:", response.status_code, response.json())

def test_suppliers():
    response = client.get("/api/v1/suppliers/")
    print("Suppliers endpoint:", response.status_code, response.json())

def test_card_configs():
    response = client.get("/api/v1/card-configs/")
    print("Card configs endpoint:", response.status_code, response.json())

if __name__ == "__main__":
    test_root()
    test_machine_types()
    test_suppliers()
    test_card_configs()