import sqlite3
import os

# Database file path
db_path = 'd:/Projects/backend/app/test.db'

print("Database Content Viewer")
print("=" * 50)

# Check if database file exists
if not os.path.exists(db_path):
    print(f"Database file not found at {db_path}")
    exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
print("1. Tables in the database:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"   - {table[0]}")

# Check suppliers
print("\n2. Suppliers:")
try:
    cursor.execute("SELECT * FROM suppliers")
    suppliers = cursor.fetchall()
    if suppliers:
        print(f"   Found {len(suppliers)} suppliers:")
        for supplier in suppliers:
            print(f"   - ID: {supplier[0]}, Name: {supplier[1]}")
    else:
        print("   No suppliers found")
except Exception as e:
    print(f"   Error reading suppliers: {e}")

# Check machines
print("\n3. Machines:")
try:
    cursor.execute("SELECT * FROM machines")
    machines = cursor.fetchall()
    if machines:
        print(f"   Found {len(machines)} machines:")
        for machine in machines:
            print(f"   - ID: {machine[0]}, Name/Model: {machine[1]}, Supplier ID: {machine[7]}")
    else:
        print("   No machines found")
except Exception as e:
    print(f"   Error reading machines: {e}")

# Check cards
print("\n4. Cards:")
try:
    cursor.execute("SELECT * FROM cards")
    cards = cursor.fetchall()
    if cards:
        print(f"   Found {len(cards)} cards:")
        for card in cards:
            print(f"   - ID: {card[0]}, Model: {card[1]}")
    else:
        print("   No cards found")
except Exception as e:
    print(f"   Error reading cards: {e}")

# Check machine_cards relationships
print("\n5. Machine-Card Relationships:")
try:
    cursor.execute("SELECT * FROM machine_cards")
    relationships = cursor.fetchall()
    if relationships:
        print(f"   Found {len(relationships)} relationships:")
        for rel in relationships:
            print(f"   - Machine ID: {rel[0]}, Card ID: {rel[1]}")
    else:
        print("   No machine-card relationships found")
except Exception as e:
    print(f"   Error reading relationships: {e}")

# Close connection
conn.close()
print("\nDatabase content viewing completed.")