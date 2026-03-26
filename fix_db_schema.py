import sqlite3
import os

DB_PATH = "temp_vulnerability_alerts.db"

def fix_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("PRAGMA table_info(organizations);")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns in 'organizations': {columns}")
        
        if 'enabled_oems' not in columns:
            print("Adding 'enabled_oems' column...")
            cursor.execute("ALTER TABLE organizations ADD COLUMN enabled_oems VARCHAR(500) DEFAULT 'ALL'")
            conn.commit()
            print("Column added successfully.")
        else:
            print("'enabled_oems' column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_schema()
