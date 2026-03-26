from sqlalchemy import create_engine, text
from config import APP_CONFIG

def migrate():
    engine = create_engine(APP_CONFIG["database_url"])
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(organizations)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'enabled_oems' not in columns:
                print("Adding enabled_oems column to organizations table...")
                conn.execute(text("ALTER TABLE organizations ADD COLUMN enabled_oems VARCHAR(500) DEFAULT 'ALL'"))
                conn.commit()
                print("Migration successful!")
            else:
                print("Column enabled_oems already exists.")
                
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
