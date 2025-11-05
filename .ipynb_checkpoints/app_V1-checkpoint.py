# app.py
import os, base64, sqlite3, uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from flask_cors import CORS

from flask import Flask, request, redirect, url_for, render_template_string, session, flash
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

# ---------- Config ----------
APP_ROOT = Path(__file__).parent
UPLOAD_FOLDER = APP_ROOT / "uploads"
CSV_PATH = UPLOAD_FOLDER / "detections.csv"
USERS_DB = APP_ROOT / "users.db"

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET", "replace_with_random_secret_in_prod")

# ---------- Helpers ----------
def init_csv():
    if not CSV_PATH.exists():
        df = pd.DataFrame(columns=["timestamp", "farmer_id", "insect", "count", "image_path"])
        df.to_csv(CSV_PATH, index=False)

def read_df():
    init_csv()
    df = pd.read_csv(CSV_PATH)
    # ensure `count` is numeric (safe conversion)
    if 'count' in df.columns:
        df['count'] = pd.to_numeric(df['count'], errors='coerce').fillna(0).astype(int)
    else:
        df['count'] = 0
    return df

def append_record(timestamp, farmer_id, insect, count, image_path):
    init_csv()
    row = {"timestamp": timestamp, "farmer_id": farmer_id, "insect": insect, "count": int(count), "image_path": str(image_path)}
    pd.DataFrame([row]).to_csv(CSV_PATH, mode="a", index=False, header=not CSV_PATH.exists())

# ---------- Users DB ----------
# devices helpers (add to top where DB functions are)
import uuid
import sqlite3

def init_devices_table():
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_name TEXT,
        device_key TEXT UNIQUE,
        farmer_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

def create_device(device_name, farmer_id):
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    # generate long random key
    device_key = uuid.uuid4().hex + uuid.uuid4().hex
    cur.execute("INSERT INTO devices (device_name, device_key, farmer_id) VALUES (?,?,?)", (device_name, device_key, farmer_id))
    conn.commit()
    cur.execute("SELECT id, device_key FROM devices WHERE device_key=?", (device_key,))
    row = cur.fetchone()
    conn.close()
    return {"id": row[0], "device_key": row[1]}

def get_all_devices():
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("SELECT id, device_name, device_key, farmer_id, created_at FROM devices ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_device_by_key(device_key):
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("SELECT id, device_name, device_key, farmer_id FROM devices WHERE device_key=?", (device_key,))
    row = cur.fetchone()
    conn.close()
    return row

def regenerate_device_key(device_id):
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    new_key = uuid.uuid4().hex + uuid.uuid4().hex
    cur.execute("UPDATE devices SET device_key=? WHERE id=?", (new_key, device_id))
    conn.commit()
    conn.close()
    return new_key

def init_users_db():
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE,
      password_hash TEXT,
      role TEXT,
      farmer_id TEXT
    );
    """)
    conn.commit()
    conn.close()

def create_sample_users():
    init_users_db()
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    # Insert admin (if not exists)
    try:
        cur.execute("INSERT INTO users (username,password_hash,role,farmer_id) VALUES (?,?,?,?)",
                    ("admin", generate_password_hash("admin123"), "admin", None))
    except sqlite3.IntegrityError:
        pass
    # Insert sample farmer
    try:
        cur.execute("INSERT INTO users (username,password_hash,role,farmer_id) VALUES (?,?,?,?)",
                    ("farmer1", generate_password_hash("pass123"), "farmer", "farmer_001"))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, role, farmer_id FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row

def get_all_farmers():
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("SELECT username, farmer_id FROM users WHERE role='farmer'")
    rows = cur.fetchall()
    conn.close()
    return rows

# Initialize
init_csv()
init_users_db()
init_devices_table()   # <-- ADD THIS
create_sample_users()


# ---------- Auth helpers ----------
def login_user(username):
    session['username'] = username

def current_user():
    uname = session.get('username')
    if not uname:
        return None
    row = get_user(uname)
    if not row:
        return None
    return {"id": row[0], "username": row[1], "role": row[3], "farmer_id": row[4]}

def logout_user():
    session.pop('username', None)

# ---------- Routes ----------
CORS(app)

@app.route("/")
def index():
    user = current_user()
    if user:
        if user.get("role") == "admin":
            return redirect(url_for("admin"))
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))



# LOGIN API (simple; uses existing users.db)
@app.route("/login_api", methods=["POST"])
def login_api():
    # Accepts form or JSON
    data = request.get_json(silent=True) or request.form
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return {"success": False, "error": "missing credentials"}, 400
    user = get_user(username)
    if not user:
        return {"success": False, "error": "invalid creds"}, 401
    _, uname, password_hash, role, farmer_id = user
    if check_password_hash(password_hash, password):
        # return farmer_id for farmer role, else admin
        return {"success": True, "role": role, "farmer_id": farmer_id}
    else:
        return {"success": False, "error": "invalid creds"}, 401

# Farmer data API (already suggested earlier but here's a robust version)
@app.route("/api/farmer_data", methods=["GET"])
def api_farmer_data():
    farmer_id = request.args.get("farmer_id")
    if not farmer_id:
        return {"records": []}
    df = read_df()
    farmer_df = df[df['farmer_id'] == farmer_id].copy()
    # produce image_url relative to host
    def make_url(p):
        if not p or pd.isna(p) or str(p) == '':
            return ""
        fname = str(p).replace("\\", "/").split("/")[-1]
        return request.host_url.rstrip("/") + "/uploads/" + fname
    farmer_df['image_url'] = farmer_df['image_path'].apply(make_url)
    return {"records": farmer_df.to_dict(orient="records")}

@app.route("/logout")
def logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for("login"))

# Dashboard: farmers see own data, admin redirected to /admin
@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    if user['role'] == 'admin':
        return redirect(url_for("admin"))  # redirect admin to admin page

    # --- Farmer Dashboard ---
    df = read_df()
    farmer_df = df[df['farmer_id'] == user['farmer_id']].copy()
    total_records = len(farmer_df)
    summary = farmer_df.groupby("insect")["count"].sum().reset_index()

    # fix image paths
    farmer_df['image_path'] = farmer_df['image_path'].apply(lambda p: str(p).replace('\\','/'))

    return render_template_string(
        DASH_HTML,
        username=user['username'],
        df=farmer_df.to_dict(orient='records'),
        summary=summary.to_dict(orient='records'),
        total_records=total_records
    )

@app.route("/admin")
def admin():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))

    df = read_df()
    summary = df.groupby("insect")["count"].sum().reset_index()
    farmers = get_all_farmers()
    devices = get_all_devices()

    return render_template_string(
        ADMIN_HTML,
        farmers=farmers,
        devices=devices,
        summary=summary.to_dict(orient='records')
    )


# Admin page: list farmers and view global stats
from flask import request, redirect, url_for, flash

@app.route("/admin/create_device", methods=["POST"])
def admin_create_device():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    device_name = request.form.get("device_name")
    farmer_id = request.form.get("farmer_id")
    if not device_name or not farmer_id:
        flash("Device name and farmer required", "danger")
        return redirect(url_for("admin"))
    res = create_device(device_name, farmer_id)
    flash(f"Device created. Key: {res['device_key'][:8]}... (copy full key above)", "success")
    return redirect(url_for("admin"))

@app.route("/admin/regenerate_key", methods=["POST"])
def admin_regenerate_key():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    device_id = request.form.get("device_id")
    if not device_id:
        flash("device_id required", "danger")
        return redirect(url_for("admin"))
    new_key = regenerate_device_key(device_id)
    flash("Key regenerated. New key (first 8): " + new_key[:8] + "...", "success")
    return redirect(url_for("admin"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = get_user(username)
        if user and check_password_hash(user[2], password):
            login_user(username)  # <-- THIS SETS SESSION
            if user[3] == "admin":
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return """
    <h2>Login</h2>
    <form action="/login" method="POST">
        <input type="text" name="username" placeholder="Username"><br><br>
        <input type="password" name="password" placeholder="Password"><br><br>
        <button type="submit">Login</button>
    </form>
    <p>Admin: admin / admin123</p>
    <p>Farmer: farmer1 / pass123</p>
    """




# Simple health
@app.route("/health")
def health():
    return {"ok": True}

# Upload endpoint - expects JSON with base64 image
# JSON format: {"farmer_id":"farmer_001","insect":"Whitefly","count":12,"image":"<base64 str>"}
@app.route("/upload", methods=["POST"])
def upload():
    # accept JSON (device_key preferred) or form-data fallback
    data = None
    try:
        data = request.get_json(force=False, silent=True)
    except Exception:
        data = None

    if data and 'device_key' in data:
        device_key = data.get('device_key')
        device = get_device_by_key(device_key)
        if not device:
            return {"error":"invalid device_key"}, 403
        # extract farmer_id from device row (device[3] per helper)
        farmer_id = device[3]
        insect = data.get("insect","unknown")
        try:
            count = int(data.get("count",0))
        except:
            count = 0
        image_b64 = data.get("image")
    else:
        # legacy form-data mode (for testing)
        farmer_id = request.form.get("farmer_id", "unknown")
        insect = request.form.get("insect", "unknown")
        try:
            count = int(request.form.get("count", 0))
        except:
            count = 0
        # file upload fallback
        if 'image' in request.files:
            f = request.files['image']
            image_b64 = None
            # save file directly
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{timestamp}_{farmer_id}.jpg"
            save_path = UPLOAD_FOLDER / filename
            f.save(save_path)
            image_path_to_save = save_path
            append_record(timestamp, farmer_id, insect, count, image_path_to_save)
            return {"status":"ok", "image_saved": str(save_path)}, 200
        else:
            image_b64 = None

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    image_path = ""
    if image_b64:
        filename = f"{timestamp}_{(farmer_id or 'unknown')}.jpg"
        image_path = UPLOAD_FOLDER / filename
        try:
            with open(image_path, "wb") as fh:
                fh.write(base64.b64decode(image_b64))
        except Exception as e:
            return {"error":"image save failed", "detail":str(e)}, 500

    # Save CSV record
    append_record(timestamp, farmer_id, insect, count, image_path)
    return {"status":"ok", "farmer_id": farmer_id, "saved": str(image_path)}, 200


@app.route('/api/upload_result', methods=['POST'])
def upload_result():
    # 1) Extract Device-Key header
    device_key = request.headers.get("Device-Key")
    if not device_key:
        return {"error": "Device-Key header missing"}, 400

    # 2) Validate device key
    device = get_device_by_key(device_key)
    if not device:
        return {"error": "invalid device_key"}, 403

    # device tuple => (id, device_name, device_key, farmer_id)
    farmer_id = device[3]

    # 3) Parse JSON
    data = request.get_json(silent=True)
    if not data:
        return {"error": "invalid or missing JSON"}, 400

    insect = data.get("insect", "unknown")
    try:
        count = int(data.get("count", 0))
    except:
        count = 0

    image_b64 = data.get("image_base64")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # 4) Decode and save image
    image_path = ""
    if image_b64:
        filename = f"{timestamp}_{farmer_id}.jpg"
        image_path = UPLOAD_FOLDER / filename
        try:
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_b64))
        except Exception as e:
            return {"error": "image save failed", "detail": str(e)}, 500

    # 5) Save detection record (CSV)
    append_record(timestamp, farmer_id, insect, count, image_path)

    return {
        "status": "ok",
        "farmer_id": farmer_id,
        "saved_image": str(image_path),
        "insect": insect,
        "count": count
    }, 200








# Serve uploads (so images are clickable)
@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    # simple static serving from uploads folder
    from flask import send_from_directory
    return send_from_directory(str(UPLOAD_FOLDER), filename)

# ---------- HTML TEMPLATES (dark theme) ----------
LOGIN_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Login - InsectDetect</title>
  <style>
    body{ background:#121212; color:#e6eef8; font-family:Arial, Helvetica, sans-serif; }
    .card{ max-width:420px; margin:8% auto; background:#1e1e1e; padding:24px; border-radius:10px; box-shadow:0 6px 18px rgba(0,0,0,0.6);}
    input{ width:100%; padding:10px; margin:8px 0; border-radius:6px; border:1px solid #333; background:#0f0f0f; color:#fff }
    button{ width:100%; padding:10px; background:#0ea5a4; color:#012; border:none; border-radius:6px; font-weight:700; }
    h2{ text-align:center; color:#e6eef8 }
    .small{ color:#9aa7b2; font-size:13px; text-align:center; margin-top:8px;}
  </style>
</head>
<body>
  <div class="card">
    <h2>InsectDetect — Login</h2>
    <form method="post">
      <input name="username" placeholder="Username" required>
      <input name="password" type="password" placeholder="Password" required>
      <button type="submit">Sign in</button>
    </form>
    <p class="small">Admin sample: <b>admin / admin123</b>  — Farmer sample: <b>farmer1 / pass123</b></p>
  </div>
</body>
</html>
"""

DASH_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Dashboard - InsectDetect</title>
  <style>
    body{ background:#0b0b0b; color:#e6eef8; font-family:Inter, Arial, sans-serif; padding:20px; }
    header{ display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;}
    .card{ background:#111; padding:14px; border-radius:10px; box-shadow:0 6px 18px rgba(0,0,0,0.6);}
    table{ width:100%; border-collapse:collapse; margin-top:10px; }
    th{ background:#0f1724; color:#9bd1f5; padding:10px; text-align:left; font-weight:700; }
    td{ padding:10px; border-bottom:1px solid #1f2937; color:#cfe8ff; vertical-align:middle;}
    img.thumb{ width:84px; height:64px; object-fit:cover; border-radius:6px; border:1px solid #2b3440; }
    .summary{ margin-top:18px; display:flex; gap:12px;}
    .chip{ background:#0f1724; padding:10px 12px; border-radius:8px;}
    a.logout{ color:#a6d8ff; text-decoration:none; font-size:14px;}
  </style>
</head>
<body>
  <header>
    <div><h1 style="margin:0">InsectDetect</h1><div style="color:#9aa7b2">Welcome, {{ username }}</div></div>
    <div><a class="logout" href="/logout">Logout</a></div>
  </header>

  <div class="card">
    <h3 style="margin:0 0 8px 0">Detected Insects ({{ total_records }})</h3>
    <table>
      <tr><th>Timestamp</th><th>Insect</th><th>Count</th><th>Image</th></tr>
      {% for row in df %}
      <tr>
        <td>{{ row.timestamp }}</td>
        <td>{{ row.insect }}</td>
        <td style="font-weight:700">{{ row.count }}</td>
        <td>
          {% if row.image_path %}
            {% set fname = row.image_path.split('/')[-1] %}
            <a href="/uploads/{{ fname }}" target="_blank">
              <img class="thumb" src="/uploads/{{ fname }}">
            </a>
          {% else %}
            -
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </table>

    <div class="summary">
      <div class="chip"><b>Summary</b></div>
    </div>

    <h4 style="margin-top:18px">Totals by Insect</h4>
    <table>
      <tr><th>Insect</th><th>Total Count</th></tr>
      {% for s in summary %}
      <tr><td>{{ s.insect }}</td><td style="font-weight:700">{{ s['count'] }}</td></tr>
      {% endfor %}
    </table>
  </div>
</body>
</html>
"""

ADMIN_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Admin - InsectDetect</title>
  <style>
    body{ background:#050506; color:#e6eef8; font-family:Inter, Arial, sans-serif; padding:20px; }
    .card{ background:#0b0b0b; padding:14px; border-radius:10px; }
    table{ width:100%; border-collapse:collapse; margin-top:10px; }
    th{ background:#0f1724; color:#9bd1f5; padding:10px; text-align:left; }
    td{ padding:10px; border-bottom:1px solid #1f2937; color:#cfe8ff;}
    img.thumb{ width:84px; height:64px; object-fit:cover; border-radius:6px;}
    .top{ display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;}
    .small{ font-size:13px; color:#9aa7b2; }
    .btn{ background:#0ea5a4; color:#012; padding:6px 10px; border-radius:6px; text-decoration:none; }
    input, select { background:#0b0b0b; color:#e6eef8; border:1px solid #222; padding:8px; border-radius:6px; }
  </style>
  <script>
    function toggleKey(id) {
      const el = document.getElementById('key-'+id);
      if (!el) return;
      if (el.dataset.visible === '0') {
        el.textContent = el.dataset.full;
        el.dataset.visible = '1';
      } else {
        el.textContent = el.dataset.mask;
        el.dataset.visible = '0';
      }
    }
  </script>
</head>
<body>
  <div class="top">
    <h2>Admin Dashboard</h2>
    <div><a href="/logout" style="color:#9bd1f5">Logout</a></div>
  </div>

  <div class="card">
    <h3>Create Device</h3>
    <form method="post" action="/admin/create_device">
      <label>Device name</label><br>
      <input name="device_name" placeholder="Field-Device-1" required>
      <label>Assign to farmer (farmer_id)</label><br>
      <select name="farmer_id" required>
        {% for f in farmers %}
          <option value="{{ f[1] }}">{{ f[0] }} — {{ f[1] }}</option>
        {% endfor %}
      </select>
      <br><br>
      <button class="btn" type="submit">Create device</button>
    </form>

    <h3 style="margin-top:18px">Devices</h3>
    <table>
      <tr><th>Device</th><th>Farmer ID</th><th>Key (click to reveal)</th><th>Created</th><th>Actions</th></tr>
      {% for d in devices %}
        <tr>
          <td>{{ d[1] }}</td>
          <td>{{ d[3] or '-' }}</td>
          <td>
            <span id="key-{{ d[0] }}" data-full="{{ d[2] }}" data-mask="{{ d[2][:6] + '...' + d[2][-6:] }}" data-visible="0">
              {{ d[2][:6] + '...' + d[2][-6:] }}
            </span>
            &nbsp;
            <a href="javascript:toggleKey('{{ d[0] }}')">toggle</a>
          </td>
          <td>{{ d[4] }}</td>
          <td>
            <form method="post" action="/admin/regenerate_key" style="display:inline">
              <input type="hidden" name="device_id" value="{{ d[0] }}">
              <button class="btn" type="submit">Regenerate Key</button>
            </form>
          </td>
        </tr>
      {% endfor %}
    </table>
  </div>
</body>
</html>
"""

# ---------- Start ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
