
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

def seed_roles():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Create Organization
    org_name = "SecOps Team"
    print(f"Creating Organization: {org_name}")
    try:
        cursor.execute("INSERT INTO organizations (name) VALUES (?)", (org_name,))
        org_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Organization '{org_name}' already exists. Fetching ID...")
        cursor.execute("SELECT id FROM organizations WHERE name=?", (org_name,))
        org_id = cursor.fetchone()[0]

    print(f"Organization ID: {org_id}")

    # 2. Define Users
    users = [
        ("owner", "owner@secops.com", "Owner"),
        ("lead", "lead@secops.com", "Team Lead"),
        ("analyst", "analyst@secops.com", "Analyst")
    ]

    password = "password123"
    pwd_hash = hash_password(password)

    for username, email, role in users:
        print(f"Creating/Updating User: {username} ({role})")
        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, organization_id)
                VALUES (?, ?, ?, ?, ?)
            """, (username, email, pwd_hash, role, org_id))
        except sqlite3.IntegrityError:
            print(f"User '{username}' already exists. Updating role/org...")
            cursor.execute("""
                UPDATE users 
                SET role=?, organization_id=?, password_hash=?
                WHERE username=?
            """, (role, org_id, pwd_hash, username))
            
    # Set owner_id for the organization
    cursor.execute("SELECT id FROM users WHERE username='owner'")
    owner_id = cursor.fetchone()[0]
    cursor.execute("UPDATE organizations SET owner_id=? WHERE id=?", (owner_id, org_id))
    print(f"Updated Organization Owner to: owner (ID: {owner_id})")

    conn.commit()
    conn.close()
    print("\nSeeding Complete!")
    print(f"Password for all accounts: {password}")

if __name__ == "__main__":
    seed_roles()
