import sqlite3

# Connect to the database
conn = sqlite3.connect('d:/Projects/backend/app/test.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in the database:")
for table in tables:
    print(f"  - {table[0]}")

# Check suppliers table
print("\nSuppliers table:")
cursor.execute("PRAGMA table_info(suppliers)")
suppliers_columns = cursor.fetchall()
print("Columns:")
for col in suppliers_columns:
    print(f"  - {col[1]} ({col[2]})")

# Check machines table
print("\nMachines table:")
cursor.execute("PRAGMA table_info(machines)")
machines_columns = cursor.fetchall()
print("Columns:")
for col in machines_columns:
    print(f"  - {col[1]} ({col[2]})")

# Check cards table
print("\nCards table:")
cursor.execute("PRAGMA table_info(cards)")
cards_columns = cursor.fetchall()
print("Columns:")
for col in cards_columns:
    print(f"  - {col[1]} ({col[2]})")

# Check machine_cards table
print("\nMachine_Cards table:")
cursor.execute("PRAGMA table_info(machine_cards)")
machine_cards_columns = cursor.fetchall()
print("Columns:")
for col in machine_cards_columns:
    print(f"  - {col[1]} ({col[2]})")

# Close connection
conn.close()
print("\nDatabase check completed.")