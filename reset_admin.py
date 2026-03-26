
import sqlite3
import hashlib
import secrets

DB_FILE = "vulnerability_alerts.db"

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${key.hex()}"

def reset_admin():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    new_password = "admin123"
    pwd_hash = hash_password(new_password)
    
    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE username='admin'")
    row = cursor.fetchone()
    
    if row:
        cursor.execute("UPDATE users SET password_hash=? WHERE username='admin'", (pwd_hash,))
        print(f"Updated 'admin' password to '{new_password}'")
    else:
        # Check for org
        cursor.execute("SELECT id FROM organizations WHERE name='Default Org'")
        org_row = cursor.fetchone()
        if not org_row:
             cursor.execute("INSERT INTO organizations (name) VALUES ('Default Org')")
             org_id = cursor.lastrowid
        else:
             org_id = org_row[0]
             
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, organization_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('admin', 'admin@example.com', pwd_hash, 'Owner', org_id))
        print(f"Created 'admin' user with password '{new_password}'")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    reset_admin()
