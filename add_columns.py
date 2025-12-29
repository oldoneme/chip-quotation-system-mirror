import sqlite3
import os

# Database path
DB_PATH = 'backend/app/test.db'

def add_columns():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Add adjusted_price column
        try:
            cursor.execute("ALTER TABLE quote_items ADD COLUMN adjusted_price FLOAT")
            print("Added 'adjusted_price' column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("'adjusted_price' column already exists.")
            else:
                raise e

        # Add adjustment_reason column
        try:
            cursor.execute("ALTER TABLE quote_items ADD COLUMN adjustment_reason TEXT")
            print("Added 'adjustment_reason' column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("'adjustment_reason' column already exists.")
            else:
                raise e

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_columns()