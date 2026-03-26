import shutil
import sqlite3
import os
import sys

# Attempt to copy the locked file using python
src = "vulnerability_alerts.db"
dst = "temp_vulnerability_alerts_v2.db"

try:
    print(f"Copying {src} to {dst}...")
    shutil.copy2(src, dst)
    print("Copy successful.")
except Exception as e:
    print(f"Copy failed: {e}")
    sys.exit(1)

# Now patching the copy
try:
    conn = sqlite3.connect(dst)
    cursor = conn.cursor()
    print("Checking schema...")
    cursor.execute("PRAGMA table_info(organizations);")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'enabled_oems' not in columns:
        print("Adding 'enabled_oems' column...")
        cursor.execute("ALTER TABLE organizations ADD COLUMN enabled_oems VARCHAR(500) DEFAULT 'ALL'")
        conn.commit()
        print("Schema patched.")
    else:
        print("Column already exists.")
    conn.close()
    
    # Atomic replace
    print("Replacing original db...")
    shutil.move(dst, src)
    print("Database repaired.")
    
except Exception as e:
    print(f"Patching failed: {e}")
