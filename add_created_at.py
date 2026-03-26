
import sqlite3
import datetime

DB_FILE = "vulnerability_alerts.db"

def add_created_at_column():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("SELECT created_at FROM vulnerabilities LIMIT 1")
        print("Column 'created_at' already exists.")
    except sqlite3.OperationalError:
        print("Column 'created_at' missing. Adding it...")
        try:
            # Add column
            cursor.execute("ALTER TABLE vulnerabilities ADD COLUMN created_at DATETIME")
            
            # Backfill with current time
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE vulnerabilities SET created_at = ?", (now,))
            
            conn.commit()
            print("Successfully added and backfilled 'created_at' column.")
        except Exception as e:
            print(f"Error adding column: {e}")
            conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_created_at_column()
