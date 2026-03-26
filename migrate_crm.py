
import sqlite3
import os

DB_FILE = "vulnerability_alerts.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print("Database not found. Initial setup will handle creation.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("Migrating database for CRM features...")
    
    # 1. Create Organizations table
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            owner_id INTEGER REFERENCES users(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("Created 'organizations' table.")
    except Exception as e:
        print(f"Error creating organizations table: {e}")

    # 2. Update Users table (add organization_id if needed, create if not exists)
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(128) NOT NULL,
            role VARCHAR(20) DEFAULT 'Analyst' NOT NULL,
            organization_id INTEGER REFERENCES organizations(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("Created/Checked 'users' table.")
        
        # Check for organization_id column in existing table
        try:
            cursor.execute("SELECT organization_id FROM users LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE users ADD COLUMN organization_id INTEGER REFERENCES organizations(id)")
            print("Added 'organization_id' to users table.")

        # Check for password_hash column
        try:
            cursor.execute("SELECT password_hash FROM users LIMIT 1")
        except sqlite3.OperationalError:
            # Add with default to handle existing rows
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(128) DEFAULT 'scrypt:32768:8:1$kPv...' NOT NULL")
            print("Added 'password_hash' to users table.")
            
    except Exception as e:
        print(f"Error updating users table: {e}")

    # 3. Create Invitations table
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(100) NOT NULL,
            organization_id INTEGER NOT NULL REFERENCES organizations(id),
            role VARCHAR(20) DEFAULT 'Analyst' NOT NULL,
            token VARCHAR(100) NOT NULL UNIQUE,
            status VARCHAR(20) DEFAULT 'Pending',
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("Created 'invitations' table.")
    except Exception as e:
        print(f"Error creating invitations table: {e}")

    # 4. Add columns to vulnerabilities table
    columns_to_add = [
        ("organization_id", "INTEGER REFERENCES organizations(id)"),
        ("assigned_to_id", "INTEGER REFERENCES users(id)"),
        ("assigned_by_id", "INTEGER REFERENCES users(id)"),
        ("assigned_at", "DATETIME"),
        ("resolution_notes", "TEXT")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            # Check if column exists
            cursor.execute(f"SELECT {col_name} FROM vulnerabilities LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            try:
                cursor.execute(f"ALTER TABLE vulnerabilities ADD COLUMN {col_name} {col_type}")
                print(f"Added column '{col_name}' to vulnerabilities.")
            except Exception as e:
                print(f"Error adding column {col_name}: {e}")
        except Exception as e:
             # Column exists, ignore
             pass

    # 5. Insert default Org and Admin
    try:
        # Check if Default Org exists
        cursor.execute("SELECT id FROM organizations WHERE name='Default Org'")
        org_row = cursor.fetchone()
        if not org_row:
            cursor.execute("INSERT INTO organizations (name) VALUES ('Default Org')")
            org_id = cursor.lastrowid
            print(f"Created 'Default Org' with ID {org_id}")
        else:
            org_id = org_row[0]

        # Check/Create Admin
        cursor.execute("SELECT id FROM users WHERE username='admin'")
        if not cursor.fetchone():
            # Default password 'admin123' (hashed) - simplified for now, usually use bcrypt
            # For this demo, let's just store plain text or simple hash. 
            # In production, use werkzeug.security.generate_password_hash
            cursor.execute(f"""
            INSERT INTO users (username, email, password_hash, role, organization_id) 
            VALUES ('admin', 'admin@example.com', 'scrypt:32768:8:1$kPv...', 'Owner', {org_id})
            """)
            print("Created default 'admin' user (Owner).")
        else:
            # Update existing admin to be Owner and belong to Default Org if not set
            cursor.execute(f"UPDATE users SET role='Owner', organization_id={org_id} WHERE username='admin' AND organization_id IS NULL")
            print("Updated existing admin user.")
            
    except Exception as e:
        print(f"Error seeding data: {e}")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
