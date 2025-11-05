# create_devices.py
import sqlite3
import uuid
from pathlib import Path

DB = Path("users.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Add devices table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT,
    device_key TEXT UNIQUE,
    farmer_id TEXT,
    created_at TEXT
);
""")
conn.commit()

# Example: create a device and assign to farmer_001 (only if none exist)
cur.execute("SELECT COUNT(1) FROM devices")
count = cur.fetchone()[0]
if count == 0:
    device_key = uuid.uuid4().hex + uuid.uuid4().hex  # long key
    cur.execute("INSERT INTO devices (device_name, device_key, farmer_id, created_at) VALUES (?,?,?,datetime('now'))",
                ("Field-Device-1", device_key, "farmer_001"))
    conn.commit()
    print("Created sample device. device_key:", device_key)
else:
    print("Devices table exists and has", count, "entries")

conn.close()
