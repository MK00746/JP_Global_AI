# app.py
import os, base64, sqlite3, uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from flask_cors import CORS

from flask import Flask, request, redirect, url_for, render_template_string, session, flash, send_from_directory
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

APP_ROOT = Path(__file__).parent
UPLOAD_FOLDER = APP_ROOT / "uploads"
CSV_PATH = UPLOAD_FOLDER / "detections.csv"
USERS_DB = APP_ROOT / "users.db"

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "replace_with_random_secret_in_prod")

def init_csv():
    if not CSV_PATH.exists():
        df = pd.DataFrame(columns=["timestamp", "farmer_id", "insect", "count", "image_path"])
        df.to_csv(CSV_PATH, index=False)

def read_df():
    init_csv()
    df = pd.read_csv(CSV_PATH)
    if 'count' in df.columns:
        df['count'] = pd.to_numeric(df['count'], errors='coerce').fillna(0).astype(int)
    else:
        df['count'] = 0
    return df

def append_record(timestamp, farmer_id, insect, count, image_path):
    init_csv()
    row = {"timestamp": timestamp, "farmer_id": farmer_id, "insect": insect, "count": int(count), "image_path": str(image_path)}
    pd.DataFrame([row]).to_csv(CSV_PATH, mode="a", index=False, header=not CSV_PATH.exists())

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
    try:
        cur.execute("INSERT INTO users (username,password_hash,role,farmer_id) VALUES (?,?,?,?)",
                    ("admin", generate_password_hash("admin123"), "admin", None))
    except sqlite3.IntegrityError:
        pass
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

init_csv()
init_users_db()
init_devices_table()
create_sample_users()

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

CORS(app)

@app.route("/")
def index():
    user = current_user()
    if user:
        if user.get("role") == "admin":
            return redirect(url_for("admin"))
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login_api", methods=["POST"])
def login_api():
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
        return {"success": True, "role": role, "farmer_id": farmer_id}
    else:
        return {"success": False, "error": "invalid creds"}, 401

@app.route("/api/farmer_data", methods=["GET"])
def api_farmer_data():
    farmer_id = request.args.get("farmer_id")
    if not farmer_id:
        return {"records": []}
    df = read_df()
    farmer_df = df[df['farmer_id'] == farmer_id].copy()
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

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    if user['role'] == 'admin':
        return redirect(url_for("admin"))

    df = read_df()
    farmer_df = df[df['farmer_id'] == user['farmer_id']].copy()
    total_records = len(farmer_df)
    summary = farmer_df.groupby("insect")["count"].sum().reset_index()

    farmer_df['image_path'] = farmer_df['image_path'].apply(lambda p: str(p).replace('\\','/'))

    return render_template_string(
        DASH_HTML,
        username=user['username'],
        farmer_id=user['farmer_id'],
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
        df=df.to_dict(orient='records'),
        summary=summary.to_dict(orient='records')
    )

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
    flash(f"Device created. Key: {res['device_key']}", "success")
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
    flash("Key regenerated. New key: " + new_key, "success")
    return redirect(url_for("admin"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = get_user(username)
        if user and check_password_hash(user[2], password):
            login_user(username)
            if user[3] == "admin":
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template_string(LOGIN_HTML)

@app.route("/health")
def health():
    return {"ok": True}

@app.route("/upload", methods=["POST"])
def upload():
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
        farmer_id = device[3]
        insect = data.get("insect","unknown")
        try:
            count = int(data.get("count",0))
        except:
            count = 0
        image_b64 = data.get("image")
    else:
        farmer_id = request.form.get("farmer_id", "unknown")
        insect = request.form.get("insect", "unknown")
        try:
            count = int(request.form.get("count", 0))
        except:
            count = 0
        if 'image' in request.files:
            f = request.files['image']
            image_b64 = None
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

    append_record(timestamp, farmer_id, insect, count, image_path)
    return {"status":"ok", "farmer_id": farmer_id, "saved": str(image_path)}, 200

@app.route('/api/upload_result', methods=['POST'])
def upload_result():
    device_key = request.headers.get("Device-Key")
    if not device_key:
        return {"error": "Device-Key header missing"}, 400

    device = get_device_by_key(device_key)
    if not device:
        return {"error": "invalid device_key"}, 403

    farmer_id = device[3]

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

    image_path = ""
    if image_b64:
        filename = f"{timestamp}_{farmer_id}.jpg"
        image_path = UPLOAD_FOLDER / filename
        try:
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_b64))
        except Exception as e:
            return {"error": "image save failed", "detail": str(e)}, 500

    append_record(timestamp, farmer_id, insect, count, image_path)

    return {
        "status": "ok",
        "farmer_id": farmer_id,
        "saved_image": str(image_path),
        "insect": insect,
        "count": count
    }, 200

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(str(UPLOAD_FOLDER), filename)

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory('static', filename)

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }
        
        body::before {
            content: '';
            position: absolute;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(255,127,80,0.15) 0%, transparent 70%);
            top: -200px;
            right: -200px;
            border-radius: 50%;
        }
        
        body::after {
            content: '';
            position: absolute;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(64,156,255,0.15) 0%, transparent 70%);
            bottom: -150px;
            left: -150px;
            border-radius: 50%;
        }
        
        .login-container {
            position: relative;
            width: 90%;
            max-width: 480px;
            z-index: 10;
        }
        
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 48px 40px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
        
        .logo-container {
            text-align: center;
            margin-bottom: 36px;
        }
        
        .logo-container img {
            width: 220px;
            height: auto;
            margin-bottom: 16px;
            filter: drop-shadow(0 4px 12px rgba(255,127,80,0.3));
        }
        
        .welcome-text {
            color: #ffffff;
            font-size: 28px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #ff7f50 0%, #409cff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: rgba(255, 255, 255, 0.6);
            text-align: center;
            font-size: 14px;
            margin-bottom: 32px;
            font-weight: 300;
        }
        
        .form-group {
            margin-bottom: 24px;
        }
        
        .form-group label {
            display: block;
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .form-group input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #ffffff;
            font-size: 15px;
            font-family: 'Poppins', sans-serif;
            transition: all 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            background: rgba(255, 255, 255, 0.08);
            border-color: #ff7f50;
            box-shadow: 0 0 0 3px rgba(255, 127, 80, 0.1);
        }
        
        .form-group input::placeholder {
            color: rgba(255, 255, 255, 0.3);
        }
        
        .btn-login {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #ff7f50 0%, #ff6b45 100%);
            border: none;
            border-radius: 12px;
            color: #ffffff;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Poppins', sans-serif;
            box-shadow: 0 4px 15px rgba(255, 127, 80, 0.3);
            margin-top: 8px;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 127, 80, 0.4);
        }
        
        .btn-login:active {
            transform: translateY(0);
        }
        
        .credentials-info {
            margin-top: 28px;
            padding-top: 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .credentials-info p {
            color: rgba(255, 255, 255, 0.5);
            font-size: 12px;
            text-align: center;
            margin-bottom: 8px;
        }
        
        .cred-box {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 10px 14px;
            margin: 6px 0;
            font-size: 13px;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .cred-box strong {
            color: #ff7f50;
        }
        
        .flash-message {
            background: rgba(255, 107, 107, 0.15);
            border: 1px solid rgba(255, 107, 107, 0.3);
            color: #ff6b6b;
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
            text-align: center;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .logo-container img {
            animation: float 3s ease-in-out infinite;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="glass-card">
            <div class="logo-container">
                <img src="/static/images/logo.png" alt="JP Global Engineering">
            </div>
            
            <h1 class="welcome-text">AI Pest & Disease Detection</h1>
            <p class="subtitle">Advanced Pest Monitoring System</p>
            
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="flash-message">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" action="/login">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" placeholder="Enter your username" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" placeholder="Enter your password" required>
                </div>
                
                <button type="submit" class="btn-login">Sign In</button>
            </form>
            
            <div class="credentials-info">
                <p>Demo Credentials:</p>
                <div class="cred-box">
                    <strong>Admin:</strong> admin / admin123
                </div>
                <div class="cred-box">
                    <strong>Farmer:</strong> farmer1 / pass123
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

DASH_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmer Dashboard - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
            min-height: 100vh;
            color: #ffffff;
        }
        
        .navbar {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 16px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .navbar-brand {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .navbar-brand img {
            height: 45px;
        }
        
        .navbar-title {
            font-size: 20px;
            font-weight: 600;
            background: linear-gradient(135deg, #ff7f50 0%, #409cff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .navbar-user {
            display: flex;
            align-items: center;
            gap: 24px;
        }
        
        .user-info {
            text-align: right;
        }
        
        .user-name {
            font-size: 14px;
            font-weight: 500;
            color: #ffffff;
        }
        
        .user-role {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
        }
        
        .btn-logout {
            padding: 8px 20px;
            background: rgba(255, 107, 107, 0.15);
            border: 1px solid rgba(255, 107, 107, 0.3);
            border-radius: 8px;
            color: #ff6b6b;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .btn-logout:hover {
            background: rgba(255, 107, 107, 0.25);
            transform: translateY(-1px);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 32px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 127, 80, 0.3);
            box-shadow: 0 8px 24px rgba(255, 127, 80, 0.15);
        }
        
        .stat-icon {
            width: 56px;
            height: 56px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 16px;
        }
        
        .stat-icon.orange {
            background: linear-gradient(135deg, rgba(255, 127, 80, 0.2) 0%, rgba(255, 127, 80, 0.05) 100%);
            color: #ff7f50;
        }
        
        .stat-icon.blue {
            background: linear-gradient(135deg, rgba(64, 156, 255, 0.2) 0%, rgba(64, 156, 255, 0.05) 100%);
            color: #409cff;
        }
        
        .stat-icon.green {
            background: linear-gradient(135deg, rgba(76, 217, 100, 0.2) 0%, rgba(76, 217, 100, 0.05) 100%);
            color: #4cd964;
        }
        
        .stat-icon.purple {
            background: linear-gradient(135deg, rgba(175, 82, 222, 0.2) 0%, rgba(175, 82, 222, 0.05) 100%);
            color: #af52de;
        }
        
        .stat-label {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.6);
            margin-bottom: 4px;
            font-weight: 400;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #ffffff;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 24px;
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }
        
        .chart-title {
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
        }
        
        .table-container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 28px;
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        thead tr {
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        th {
            padding: 12px 16px;
            text-align: left;
            font-size: 13px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.7);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
        }
        
        tbody tr {
            transition: all 0.2s ease;
        }
        
        tbody tr:hover {
            background: rgba(255, 255, 255, 0.03);
        }
        
        .image-thumb {
            width: 80px;
            height: 60px;
            object-fit: cover;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .image-thumb:hover {
            transform: scale(1.05);
            border-color: #ff7f50;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(10px);
        }
        
        .modal-content {
            position: relative;
            margin: 5% auto;
            max-width: 800px;
            animation: zoomIn 0.3s ease;
        }
        
        .modal-content img {
            width: 100%;
            border-radius: 12px;
        }
        
        .close-modal {
            position: absolute;
            top: -40px;
            right: 0;
            color: #fff;
            font-size: 32px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .close-modal:hover {
            color: #ff7f50;
        }
        
        @keyframes zoomIn {
            from {
                transform: scale(0.8);
                opacity: 0;
            }
            to {
                transform: scale(1);
                opacity: 1;
            }
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .badge-count {
            background: rgba(255, 127, 80, 0.2);
            color: #ff7f50;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: rgba(255, 255, 255, 0.5);
        }
        
        .empty-state i {
            font-size: 64px;
            margin-bottom: 16px;
            opacity: 0.3;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 16px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .navbar {
                padding: 12px 16px;
            }
            
            .navbar-brand img {
                height: 35px;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-brand">
            <img src="/static/images/logo.png" alt="JP Global">
            <span class="navbar-title">AI Insect Detection Dashboard</span>
        </div>
        <div class="navbar-user">
            <div class="user-info">
                <div class="user-name">{{ username }}</div>
                <div class="user-role">Farmer Dashboard</div>
            </div>
            <a href="/logout" class="btn-logout">
                <i class="fas fa-sign-out-alt"></i> Logout
            </a>
        </div>
    </nav>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon orange">
                    <i class="fas fa-bug"></i>
                </div>
                <div class="stat-label">Total Detections</div>
                <div class="stat-value">{{ total_records }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon blue">
                    <i class="fas fa-layer-group"></i>
                </div>
                <div class="stat-label">Insect Types</div>
                <div class="stat-value">{{ summary|length }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon green">
                    <i class="fas fa-chart-line"></i>
                </div>
                <div class="stat-label">Total Count</div>
                <div class="stat-value" id="totalCount">0</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon purple">
                    <i class="fas fa-seedling"></i>
                </div>
                <div class="stat-label">Farm ID</div>
                <div class="stat-value" style="font-size: 18px;">{{ farmer_id }}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-chart-pie"></i> Insect Distribution</h2>
            </div>
            <canvas id="insectPieChart" style="max-height: 300px;"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-chart-bar"></i> Detection Analysis</h2>
            </div>
            <canvas id="insectBarChart" style="max-height: 350px;"></canvas>
        </div>
        
        <div class="table-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-table"></i> Detection Records</h2>
            </div>
            
            {% if df|length > 0 %}
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Insect Type</th>
                        <th>Count</th>
                        <th>Image</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in df %}
                    <tr>
                        <td>{{ row.timestamp }}</td>
                        <td>{{ row.insect }}</td>
                        <td><span class="badge badge-count">{{ row.count }}</span></td>
                        <td>
                            {% if row.image_path %}
                                {% set fname = row.image_path.split('/')[-1] %}
                                <img src="/uploads/{{ fname }}" class="image-thumb" onclick="openModal('/uploads/{{ fname }}')" alt="Detection">
                            {% else %}
                                <span style="color: rgba(255,255,255,0.3);">No image</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No detection records yet</p>
            </div>
            {% endif %}
        </div>
    </div>
    
    <div id="imageModal" class="modal" onclick="closeModal()">
        <div class="modal-content">
            <span class="close-modal">&times;</span>
            <img id="modalImage" src="" alt="Full size">
        </div>
    </div>
    
    <script>
        const summaryData = {{ summary|tojson }};
        
        let totalCount = 0;
        summaryData.forEach(item => {
            totalCount += item.count;
        });
        document.getElementById('totalCount').textContent = totalCount;
        
        const pieCtx = document.getElementById('insectPieChart').getContext('2d');
        const pieChart = new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: summaryData.map(item => item.insect),
                datasets: [{
                    data: summaryData.map(item => item.count),
                    backgroundColor: [
                        'rgba(255, 127, 80, 0.8)',
                        'rgba(64, 156, 255, 0.8)',
                        'rgba(76, 217, 100, 0.8)',
                        'rgba(175, 82, 222, 0.8)',
                        'rgba(255, 204, 0, 0.8)',
                        'rgba(255, 107, 107, 0.8)'
                    ],
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            padding: 15,
                            font: {
                                size: 13,
                                family: 'Poppins'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            family: 'Poppins'
                        },
                        bodyFont: {
                            size: 13,
                            family: 'Poppins'
                        }
                    }
                }
            }
        });
        
        const barCtx = document.getElementById('insectBarChart').getContext('2d');
        const barChart = new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: summaryData.map(item => item.insect),
                datasets: [{
                    label: 'Detection Count',
                    data: summaryData.map(item => item.count),
                    backgroundColor: 'rgba(255, 127, 80, 0.6)',
                    borderColor: 'rgba(255, 127, 80, 1)',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            font: {
                                family: 'Poppins'
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            font: {
                                family: 'Poppins'
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            font: {
                                family: 'Poppins'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            family: 'Poppins'
                        },
                        bodyFont: {
                            size: 13,
                            family: 'Poppins'
                        }
                    }
                }
            }
        });
        
        function openModal(imageSrc) {
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImage').src = imageSrc;
        }
        
        function closeModal() {
            document.getElementById('imageModal').style.display = 'none';
        }
    </script>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
            min-height: 100vh;
            color: #ffffff;
        }
        
        .navbar {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 16px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .navbar-brand {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .navbar-brand img {
            height: 45px;
        }
        
        .navbar-title {
            font-size: 20px;
            font-weight: 600;
            background: linear-gradient(135deg, #ff7f50 0%, #409cff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .navbar-user {
            display: flex;
            align-items: center;
            gap: 24px;
        }
        
        .user-info {
            text-align: right;
        }
        
        .user-name {
            font-size: 14px;
            font-weight: 500;
            color: #ffffff;
        }
        
        .user-role {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
        }
        
        .btn-logout {
            padding: 8px 20px;
            background: rgba(255, 107, 107, 0.15);
            border: 1px solid rgba(255, 107, 107, 0.3);
            border-radius: 8px;
            color: #ff6b6b;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .btn-logout:hover {
            background: rgba(255, 107, 107, 0.25);
            transform: translateY(-1px);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 32px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 127, 80, 0.3);
            box-shadow: 0 8px 24px rgba(255, 127, 80, 0.15);
        }
        
        .stat-icon {
            width: 56px;
            height: 56px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 16px;
        }
        
        .stat-icon.orange {
            background: linear-gradient(135deg, rgba(255, 127, 80, 0.2) 0%, rgba(255, 127, 80, 0.05) 100%);
            color: #ff7f50;
        }
        
        .stat-icon.blue {
            background: linear-gradient(135deg, rgba(64, 156, 255, 0.2) 0%, rgba(64, 156, 255, 0.05) 100%);
            color: #409cff;
        }
        
        .stat-icon.green {
            background: linear-gradient(135deg, rgba(76, 217, 100, 0.2) 0%, rgba(76, 217, 100, 0.05) 100%);
            color: #4cd964;
        }
        
        .stat-icon.gold {
            background: linear-gradient(135deg, rgba(255, 204, 0, 0.2) 0%, rgba(255, 204, 0, 0.05) 100%);
            color: #ffcc00;
        }
        
        .stat-label {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.6);
            margin-bottom: 4px;
            font-weight: 400;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #ffffff;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 24px;
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }
        
        .chart-title {
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
        }
        
        .section-title {
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #ffffff;
        }
        
        .form-container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 24px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            color: #ffffff;
            font-size: 14px;
            font-family: 'Poppins', sans-serif;
            transition: all 0.3s ease;
        }
        
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            background: rgba(255, 255, 255, 0.08);
            border-color: #ff7f50;
            box-shadow: 0 0 0 3px rgba(255, 127, 80, 0.1);
        }
        
        .btn-primary {
            padding: 12px 28px;
            background: linear-gradient(135deg, #ff7f50 0%, #ff6b45 100%);
            border: none;
            border-radius: 10px;
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Poppins', sans-serif;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 127, 80, 0.3);
        }
        
        .btn-secondary {
            padding: 8px 16px;
            background: rgba(64, 156, 255, 0.15);
            border: 1px solid rgba(64, 156, 255, 0.3);
            border-radius: 8px;
            color: #409cff;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Poppins', sans-serif;
        }
        
        .btn-secondary:hover {
            background: rgba(64, 156, 255, 0.25);
        }
        
        .table-container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 28px;
            overflow-x: auto;
            margin-bottom: 24px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        thead tr {
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        th {
            padding: 12px 16px;
            text-align: left;
            font-size: 13px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.7);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
        }
        
        tbody tr {
            transition: all 0.2s ease;
        }
        
        tbody tr:hover {
            background: rgba(255, 255, 255, 0.03);
        }
        
        .key-display {
            font-family: 'Courier New', monospace;
            background: rgba(0, 0, 0, 0.3);
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
        }
        
        .key-actions {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .copy-btn {
            background: rgba(76, 217, 100, 0.15);
            border: 1px solid rgba(76, 217, 100, 0.3);
            color: #4cd964;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
        }
        
        .copy-btn:hover {
            background: rgba(76, 217, 100, 0.25);
        }
        
        .flash-messages {
            margin-bottom: 24px;
        }
        
        .flash-message {
            padding: 14px 18px;
            border-radius: 10px;
            margin-bottom: 12px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .flash-message.success {
            background: rgba(76, 217, 100, 0.15);
            border: 1px solid rgba(76, 217, 100, 0.3);
            color: #4cd964;
        }
        
        .flash-message.danger {
            background: rgba(255, 107, 107, 0.15);
            border: 1px solid rgba(255, 107, 107, 0.3);
            color: #ff6b6b;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 16px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .navbar {
                padding: 12px 16px;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-brand">
            <img src="/static/images/logo.png" alt="JP Global">
            <span class="navbar-title">Admin Control Panel</span>
        </div>
        <div class="navbar-user">
            <div class="user-info">
                <div class="user-name">Administrator</div>
                <div class="user-role">Admin Dashboard</div>
            </div>
            <a href="/logout" class="btn-logout">
                <i class="fas fa-sign-out-alt"></i> Logout
            </a>
        </div>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="flash-messages">
                    {% for message in messages %}
                        <div class="flash-message success">
                            <i class="fas fa-check-circle"></i>
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon orange">
                    <i class="fas fa-bug"></i>
                </div>
                <div class="stat-label">Total Detections</div>
                <div class="stat-value" id="totalDetections">{{ df|length }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon blue">
                    <i class="fas fa-users"></i>
                </div>
                <div class="stat-label">Active Farmers</div>
                <div class="stat-value">{{ farmers|length }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon green">
                    <i class="fas fa-layer-group"></i>
                </div>
                <div class="stat-label">Insect Types</div>
                <div class="stat-value">{{ summary|length }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon gold">
                    <i class="fas fa-microchip"></i>
                </div>
                <div class="stat-label">Registered Devices</div>
                <div class="stat-value">{{ devices|length }}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-chart-pie"></i> Global Insect Distribution</h2>
            </div>
            <canvas id="insectPieChart" style="max-height: 300px;"></canvas>
        </div>
        
        <div class="form-container">
            <h2 class="section-title"><i class="fas fa-plus-circle"></i> Create New Device</h2>
            <form method="POST" action="/admin/create_device">
                <div class="form-group">
                    <label for="device_name">Device Name</label>
                    <input type="text" id="device_name" name="device_name" placeholder="e.g., Field-Device-01" required>
                </div>
                
                <div class="form-group">
                    <label for="farmer_id">Assign to Farmer</label>
                    <select id="farmer_id" name="farmer_id" required>
                        <option value="">-- Select Farmer --</option>
                        {% for f in farmers %}
                            <option value="{{ f[1] }}">{{ f[0] }} ({{ f[1] }})</option>
                        {% endfor %}
                    </select>
                </div>
                
                <button type="submit" class="btn-primary">
                    <i class="fas fa-plus"></i> Create Device
                </button>
            </form>
        </div>
        
        <div class="table-container">
            <h2 class="section-title"><i class="fas fa-microchip"></i> Device Management</h2>
            <table>
                <thead>
                    <tr>
                        <th>Device Name</th>
                        <th>Farmer ID</th>
                        <th>Device Key</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for d in devices %}
                    <tr>
                        <td><strong>{{ d[1] }}</strong></td>
                        <td>{{ d[3] or '-' }}</td>
                        <td>
                            <div class="key-actions">
                                <span class="key-display" id="key-{{ d[0] }}" onclick="toggleKey('{{ d[0] }}', '{{ d[2] }}')">
                                    {{ d[2][:8] }}...{{ d[2][-8:] }}
                                </span>
                                <button class="copy-btn" onclick="copyKey('{{ d[2] }}')">
                                    <i class="fas fa-copy"></i> Copy
                                </button>
                            </div>
                        </td>
                        <td>{{ d[4] }}</td>
                        <td>
                            <form method="POST" action="/admin/regenerate_key" style="display: inline;">
                                <input type="hidden" name="device_id" value="{{ d[0] }}">
                                <button type="submit" class="btn-secondary">
                                    <i class="fas fa-sync-alt"></i> Regenerate
                                </button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        const summaryData = {{ summary|tojson }};
        
        const pieCtx = document.getElementById('insectPieChart').getContext('2d');
        const pieChart = new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: summaryData.map(item => item.insect),
                datasets: [{
                    data: summaryData.map(item => item.count),
                    backgroundColor: [
                        'rgba(255, 127, 80, 0.8)',
                        'rgba(64, 156, 255, 0.8)',
                        'rgba(76, 217, 100, 0.8)',
                        'rgba(175, 82, 222, 0.8)',
                        'rgba(255, 204, 0, 0.8)',
                        'rgba(255, 107, 107, 0.8)'
                    ],
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            padding: 15,
                            font: {
                                size: 13,
                                family: 'Poppins'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            family: 'Poppins'
                        },
                        bodyFont: {
                            size: 13,
                            family: 'Poppins'
                        }
                    }
                }
            }
        });
        
        const keyStates = {};
        
        function toggleKey(id, fullKey) {
            const element = document.getElementById('key-' + id);
            if (!keyStates[id]) {
                element.textContent = fullKey;
                keyStates[id] = true;
            } else {
                element.textContent = fullKey.substring(0, 8) + '...' + fullKey.substring(fullKey.length - 8);
                keyStates[id] = false;
            }
        }
        
        function copyKey(key) {
            navigator.clipboard.writeText(key).then(() => {
                alert('Device key copied to clipboard!');
            });
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
