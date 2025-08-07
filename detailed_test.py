import requests
import json
import time

print("Testing API endpoints...")
print("=" * 50)

# Wait a moment for the server to start
time.sleep(2)

try:
    # Test health check endpoint
    print("1. Testing health check endpoint...")
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
except requests.exceptions.ConnectionError:
    print("   Error: Cannot connect to the backend server. Make sure it's running.")
    print()
except Exception as e:
    print(f"   Error: {e}")
    print()

try:
    # Test suppliers endpoint
    print("2. Testing suppliers endpoint...")
    response = requests.get("http://localhost:8000/api/v1/suppliers/", timeout=5)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        suppliers = response.json()
        print(f"   Number of suppliers: {len(suppliers)}")
        if suppliers:
            print(f"   First supplier: {suppliers[0]}")
    else:
        print(f"   Error response: {response.text}")
    print()
except requests.exceptions.ConnectionError:
    print("   Error: Cannot connect to the backend server. Make sure it's running.")
    print()
except Exception as e:
    print(f"   Error: {e}")
    print()

try:
    # Test machines endpoint
    print("3. Testing machines endpoint...")
    response = requests.get("http://localhost:8000/api/v1/machines/", timeout=5)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        machines = response.json()
        print(f"   Number of machines: {len(machines)}")
        if machines:
            print(f"   First machine: {machines[0]}")
    else:
        print(f"   Error response: {response.text}")
    print()
except requests.exceptions.ConnectionError:
    print("   Error: Cannot connect to the backend server. Make sure it's running.")
    print()
except Exception as e:
    print(f"   Error: {e}")
    print()

try:
    # Test cards endpoint
    print("4. Testing cards endpoint...")
    response = requests.get("http://localhost:8000/api/v1/cards/", timeout=5)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        cards = response.json()
        print(f"   Number of cards: {len(cards)}")
        if cards:
            print(f"   First card: {cards[0]}")
    else:
        print(f"   Error response: {response.text}")
    print()
except requests.exceptions.ConnectionError:
    print("   Error: Cannot connect to the backend server. Make sure it's running.")
    print()
except Exception as e:
    print(f"   Error: {e}")
    print()

print("API testing completed.")