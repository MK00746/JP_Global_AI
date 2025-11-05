import sqlite3

conn = sqlite3.connect("users.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE,
  password TEXT,
  role TEXT,
  farmer_id TEXT
)
""")

# Create admin
cur.execute("INSERT OR IGNORE INTO users (username, password, role, farmer_id) VALUES (?,?,?,?)",
            ("admin", "admin123", "admin", None))

# Example farmer user
cur.execute("INSERT OR IGNORE INTO users (username, password, role, farmer_id) VALUES (?,?,?,?)",
            ("farmer1", "pass123", "farmer", "farmer_001"))

conn.commit()
conn.close()

print("Users created.")
