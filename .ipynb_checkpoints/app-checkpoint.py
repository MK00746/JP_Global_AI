# updated_app_py.py - JP Global InsectDetect with Professional Sidebar Navigation
import os, base64, sqlite3, uuid, json
from datetime import datetime, timedelta
from pathlib import Path
from flask_cors import CORS
from flask import Flask, request, redirect, url_for, render_template_string, session, flash, send_from_directory, jsonify
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# App Configuration
APP_ROOT = Path(__file__).parent
UPLOAD_FOLDER = APP_ROOT / "uploads"
USERS_DB = APP_ROOT / "users.db"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "replace_with_random_secret_in_prod")
CORS(app)

# Database Helper Functions
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
    cur.execute("SELECT id, username, farmer_id FROM users WHERE role='farmer'")
    rows = cur.fetchall()
    conn.close()
    return rows

def create_farmer(username, password, farmer_id):
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username,password_hash,role,farmer_id) VALUES (?,?,?,?)",
                    (username, generate_password_hash(password), "farmer", farmer_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# Device Management Functions
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

def get_farmer_devices(farmer_id):
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("SELECT id, device_name, device_key, farmer_id, created_at FROM devices WHERE farmer_id=? ORDER BY created_at DESC", (farmer_id,))
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

def get_device_by_id(device_id):
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("SELECT id, device_name, device_key, farmer_id FROM devices WHERE id=?", (device_id,))
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

# Supabase Data Functions
def load_records(farmer_id=None, device_id=None):
    """Load records from Supabase, optionally filtered by farmer_id or device_id"""
    try:
        if device_id:
            res = supabase.table("insect_records").select("*").eq("device_id", str(device_id)).order("timestamp", desc=True).execute()
        elif farmer_id:
            res = supabase.table("insect_records").select("*").eq("farmer_id", farmer_id).order("timestamp", desc=True).execute()
        else:
            res = supabase.table("insect_records").select("*").order("timestamp", desc=True).execute()
        return res.data or []
    except Exception as e:
        print("Supabase load_records error:", e)
        return []

def append_record(timestamp, farmer_id, detections_json, image_url, device_id=None):
    """Append record to Supabase with detections stored as JSON"""
    try:
        record = {
            "timestamp": timestamp,
            "farmer_id": farmer_id,
            "detections": detections_json,  # JSON object or string
            "image_url": image_url
        }
        if device_id:
            record["device_id"] = str(device_id)
        
        supabase.table("insect_records").insert(record).execute()
    except Exception as e:
        print(f"Error inserting record: {e}")

def upload_image_to_supabase(filename: str, data: bytes):
    """Upload image to Supabase storage"""
    bucket = "insect-images"
    file_path = f"insects/{filename}"
    
    try:
        supabase.storage.from_(bucket).upload(file_path, data, {
            "content-type": "image/jpeg"
        })
        public_url = supabase.storage.from_(bucket).get_public_url(file_path)
        # result of get_public_url has structure {"publicURL": "..."} in some sdk versions; handle both
        if isinstance(public_url, dict):
            return public_url.get("publicURL") or public_url.get("public_url") or public_url.get("url")
        return public_url
    except Exception as e:
        print(f"Upload error: {e}")
        return None

def list_images_from_supabase():
    """List all images from Supabase storage"""
    bucket = "insect-images"
    try:
        files = supabase.storage.from_(bucket).list("insects/")
        image_list = []
        for file in files:
            filename = file['name']
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_url = supabase.storage.from_(bucket).get_public_url(f"insects/{filename}")
                # normalize structure
                if isinstance(image_url, dict):
                    url = image_url.get("publicURL") or image_url.get("public_url") or image_url.get("url")
                else:
                    url = image_url
                image_list.append({
                    'filename': filename,
                    'url': url
                })
        return image_list
    except Exception as e:
        print(f"Error listing images: {e}")
        return []

# Server-side normalization so templates that expect row.insect and row.count keep working
def normalize_records(records):
    """
    For each record (dict-like from supabase), add:
      - record['insect']    : string summary like "whiteflies:5, aphids:2"
      - record['count']     : int total count
    """
    out = []
    for r in records:
        rec = dict(r)  # shallow copy
        detections = rec.get("detections", {})
        # sometimes supabase returns JSON string; parse if necessary
        if isinstance(detections, str):
            try:
                detections = json.loads(detections)
            except:
                detections = {}
        # ensure dict
        if not isinstance(detections, dict):
            detections = {}
        # create summary and count
        parts = []
        total = 0
        for k, v in detections.items():
            try:
                c = int(v)
            except:
                try:
                    c = int(float(v))
                except:
                    c = 0
            if c > 0:
                parts.append(f"{k}:{c}")
                total += c
        rec['insect'] = ", ".join(parts) if parts else "N/A"
        rec['count'] = total
        out.append(rec)
    return out

# Session Management
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

# Initialize Database
init_users_db()
create_sample_users()

# Routes
@app.route("/")
def index():
    user = current_user()
    if user:
        if user.get("role") == "admin":
            return redirect(url_for("admin_overview"))
        return redirect(url_for("farmer_overview"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = get_user(username)
        if user and check_password_hash(user[2], password):
            login_user(username)
            if user[3] == "admin":
                return redirect(url_for("admin_overview"))
            else:
                return redirect(url_for("farmer_overview"))
        else:
            flash("Invalid credentials", "danger")
    
    from html_templates import LOGIN_HTML
    return render_template_string(LOGIN_HTML)

@app.route("/logout")
def logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for("login"))

# ==================== ADMIN ROUTES ====================
@app.route("/admin/overview")
def admin_overview():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    
    records = load_records()
    devices = get_all_devices()
    farmers = get_all_farmers()
    
    total_detections = len(records)
    total_devices = len(devices)
    total_farmers = len(farmers)
    
    # Parse detections and calculate totals
    insect_totals = {"whiteflies": 0, "aphids": 0, "thrips": 0, "beetle": 0, "fungus gnats": 0}
    total_insects = 0
    
    for record in records:
        detections = record.get("detections", {})
        if detections is None:
            try:
                detections = json.loads(detections)
            except:
                detections = {}
        for insect, count in detections.items():
            try:
                c = int(count)
            except:
                c = 0
            insect_totals[insect] = insect_totals.get(insect, 0) + c
            total_insects += c
    
    insect_summary = [{"insect": k, "count": v} for k, v in insect_totals.items() if v > 0]
    
    from html_templates import ADMIN_OVERVIEW_HTML
    return render_template_string(ADMIN_OVERVIEW_HTML, 
                                   username=user['username'],
                                   total_detections=total_detections,
                                   total_devices=total_devices,
                                   total_farmers=total_farmers,
                                   total_insects=total_insects,
                                   insect_summary=insect_summary)

@app.route("/admin/devices")
def admin_devices():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    
    devices = get_all_devices()
    farmers = get_all_farmers()
    
    from html_templates import ADMIN_DEVICES_HTML
    return render_template_string(ADMIN_DEVICES_HTML, 
                                   username=user['username'],
                                   devices=devices,
                                   farmers=farmers)

@app.route("/admin/device/<int:device_id>/analytics")
def admin_device_analytics(device_id):
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    
    device = get_device_by_id(device_id)
    if not device:
        flash("Device not found", "danger")
        return redirect(url_for("admin_devices"))
    
    records = load_records(device_id=device_id)
    
    # parse detections for summary
    insect_totals = {"whiteflies": 0, "aphids": 0, "thrips": 0, "beetle": 0, "fungus gnats": 0}
    for record in records:
        detections = record.get("detections", {})
        if isinstance(detections, str):
            try:
                detections = json.loads(detections)
            except:
                detections = {}
        for insect, count in detections.items():
            try:
                c = int(count)
            except:
                c = 0
            insect_totals[insect] = insect_totals.get(insect, 0) + c
    
    summary = [{"insect": k, "count": v} for k, v in insect_totals.items() if v > 0]
    
    # normalize for template compatibility
    records_normalized = normalize_records(records)
    
    from html_templates import ADMIN_DEVICE_ANALYTICS_HTML
    return render_template_string(ADMIN_DEVICE_ANALYTICS_HTML,
                                   username=user['username'],
                                   device=device,
                                   records=records_normalized,
                                   summary=summary)

@app.route("/admin/dataset")
def admin_dataset():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    
    farmers = get_all_farmers()
    selected_farmer = request.args.get("farmer_id", "")
    
    if selected_farmer:
        records = load_records(farmer_id=selected_farmer)
    else:
        records = load_records()
    
    records_normalized = normalize_records(records)
    
    from html_templates import ADMIN_DATASET_HTML
    return render_template_string(ADMIN_DATASET_HTML,
                                   username=user['username'],
                                   records=records_normalized,
                                   farmers=farmers,
                                   selected_farmer=selected_farmer)

@app.route("/admin/images")
def admin_images():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    
    farmers = get_all_farmers()
    selected_farmer = request.args.get("farmer_id", "")
    
    if selected_farmer:
        records = load_records(farmer_id=selected_farmer)
    else:
        records = load_records()
    
    # Filter records with images only
    records_with_images = [r for r in records if r.get("image_url")]
    records_normalized = normalize_records(records_with_images)
    
    # list available images from supabase storage for linking (used by admin form)
    available_images = list_images_from_supabase()
    
    from html_templates import ADMIN_IMAGES_HTML
    return render_template_string(ADMIN_IMAGES_HTML,
                                   username=user['username'],
                                   records=records_normalized,
                                   farmers=farmers,
                                   selected_farmer=selected_farmer,
                                   available_images=available_images)

@app.route("/admin/users")
def admin_users():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    
    farmers = get_all_farmers()
    
    from html_templates import ADMIN_USERS_HTML
    return render_template_string(ADMIN_USERS_HTML,
                                   username=user['username'],
                                   farmers=farmers)

@app.route("/admin/create_farmer", methods=["POST"])
def admin_create_farmer():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    
    username = request.form.get("username")
    password = request.form.get("password")
    farmer_id = request.form.get("farmer_id")
    
    if not username or not password or not farmer_id:
        flash("All fields are required", "danger")
        return redirect(url_for("admin_users"))
    
    success = create_farmer(username, password, farmer_id)
    if success:
        flash(f"Farmer account created: {username}", "success")
    else:
        flash("Username already exists", "danger")
    
    return redirect(url_for("admin_users"))

@app.route("/admin/create_device", methods=["POST"])
def admin_create_device():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    
    device_name = request.form.get("device_name")
    farmer_id = request.form.get("farmer_id")
    
    if not device_name or not farmer_id:
        flash("Device name and farmer required", "danger")
        return redirect(url_for("admin_devices"))
    
    res = create_device(device_name, farmer_id)
    flash(f"Device created: {device_name} | Key: {res['device_key']}", "success")
    return redirect(url_for("admin_devices"))

@app.route("/admin/regenerate_key", methods=["POST"])
def admin_regenerate_key():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    
    device_id = request.form.get("device_id")
    if not device_id:
        flash("device_id required", "danger")
        return redirect(url_for("admin_devices"))
    
    new_key = regenerate_device_key(device_id)
    flash(f"Key regenerated. New key: {new_key}", "success")
    return redirect(url_for("admin_devices"))

# ==================== FARMER ROUTES ====================
@app.route("/farmer/overview")
def farmer_overview():
    user = current_user()
    if not user or user['role'] != 'farmer':
        return redirect(url_for("login"))
    
    records = load_records(farmer_id=user['farmer_id'])
    
    # Parse detections
    insect_totals = {"whiteflies": 0, "aphids": 0, "thrips": 0, "beetle": 0, "fungus gnats": 0}
    total_count = 0
    
    for record in records:
        detections = record.get("detections", {})
        if isinstance(detections, str):
            try:
                detections = json.loads(detections)
            except:
                detections = {}
        for insect, count in detections.items():
            try:
                c = int(count)
            except:
                c = 0
            insect_totals[insect] = insect_totals.get(insect, 0) + c
            total_count += c
    
    # Find top insect
    top_insect = max(insect_totals, key=insect_totals.get) if any(insect_totals.values()) else "N/A"
    top_count = insect_totals.get(top_insect, 0)
    
    insect_summary = [{"insect": k, "count": v} for k, v in insect_totals.items() if v > 0]
    
    from html_templates import FARMER_OVERVIEW_HTML
    return render_template_string(FARMER_OVERVIEW_HTML,
                                   username=user['username'],
                                   farmer_id=user['farmer_id'],
                                   total_detections=len(records),
                                   total_count=total_count,
                                   top_insect=top_insect,
                                   top_count=top_count,
                                   insect_summary=insect_summary)

@app.route("/farmer/analysis")
def farmer_analysis():
    user = current_user()
    if not user or user['role'] != 'farmer':
        return redirect(url_for("login"))
    
    records = load_records(farmer_id=user['farmer_id'])
    records_normalized = normalize_records(records)
    
    from html_templates import FARMER_ANALYSIS_HTML
    return render_template_string(FARMER_ANALYSIS_HTML,
                                   username=user['username'],
                                   farmer_id=user['farmer_id'],
                                   records=records_normalized)

@app.route("/farmer/dataset")
def farmer_dataset():
    user = current_user()
    if not user or user['role'] != 'farmer':
        return redirect(url_for("login"))
    
    devices = get_farmer_devices(user['farmer_id'])
    selected_device = request.args.get("device_id", "")
    
    if selected_device:
        records = load_records(device_id=selected_device)
    else:
        records = load_records(farmer_id=user['farmer_id'])
    
    records_normalized = normalize_records(records)
    
    from html_templates import FARMER_DATASET_HTML
    return render_template_string(FARMER_DATASET_HTML,
                                   username=user['username'],
                                   records=records_normalized,
                                   devices=devices,
                                   selected_device=selected_device)

@app.route("/farmer/images")
def farmer_images():
    user = current_user()
    if not user or user['role'] != 'farmer':
        return redirect(url_for("login"))
    
    devices = get_farmer_devices(user['farmer_id'])
    selected_device = request.args.get("device_id", "")
    
    if selected_device:
        records = load_records(device_id=selected_device)
    else:
        records = load_records(farmer_id=user['farmer_id'])
    
    # Filter records with images only
    records_with_images = [r for r in records if r.get("image_url")]
    records_normalized = normalize_records(records_with_images)
    
    from html_templates import FARMER_IMAGES_HTML
    return render_template_string(FARMER_IMAGES_HTML,
                                   username=user['username'],
                                   records=records_normalized,
                                   devices=devices,
                                   selected_device=selected_device)

# ==================== API ROUTES ====================
from dateutil import parser

@app.route("/api/analysis_data")
def api_analysis_data():
    farmer_id = request.args.get("farmer_id")
    days = int(request.args.get("days", 7))

    # ❗ FIX TABLE NAME
    db = supabase.table("insect_records") \
        .select("*") \
        .eq("farmer_id", farmer_id) \
        .order("timestamp", desc=False) \
        .execute()

    records = db.data or []

    if not records:
        return jsonify({
            "labels": [],
            "whiteflies": [],
            "aphids": [],
            "fungus_gnat": [],
            "beetles": [],
            "thrips": []
        })

    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # ❗ FIX TIMESTAMP PARSING (ISO 8601)
    filtered = []
    for r in records:
        try:
            ts = parse(r["timestamp"])
            if ts >= cutoff_date:
                filtered.append(r)
        except:
            continue

    # Prepare lists for graph
    labels = [parse(r["timestamp"]).strftime("%Y-%m-%d") for r in filtered]
    whiteflies = [r["raw_meta"]["whiteflies"] for r in filtered]
    aphids = [r["raw_meta"]["aphids"] for r in filtered]
    fungus_gnat = [r["raw_meta"]["fungus_gnat"] for r in filtered]
    beetles = [r["raw_meta"]["beetles"] for r in filtered]
    thrips = [r["raw_meta"]["thrips"] for r in filtered]

    return jsonify({
        "labels": labels,
        "whiteflies": whiteflies,
        "aphids": aphids,
        "fungus_gnat": fungus_gnat,
        "beetles": beetles,
        "thrips": thrips
    })



@app.route('/api/upload_result', methods=['POST'])
def upload_result():
    """Device upload endpoint with device key authentication - supports multiple insect detections"""
    device_key = request.headers.get("Device-Key")
    if not device_key:
        return {"error": "Device-Key header missing"}, 400
    
    device = get_device_by_key(device_key)
    if not device:
        return {"error": "invalid device_key"}, 403
    
    device_id = device[0]
    farmer_id = device[3]
    
    data = request.get_json(silent=True)
    if not data:
        return {"error": "invalid or missing JSON"}, 400
    
    # Expect detections as JSON object: {"whiteflies": 5, "aphids": 2, "thrips": 3}
    detections = data.get("detections", {})
    if not isinstance(detections, dict):
        return {"error": "detections must be a JSON object"}, 400
    
    image_b64 = data.get("image_base64") or data.get("image_b64")
    timestamp = parse(r['timestamp'])

    
    image_url = ""
    if image_b64:
        filename = f"{parse(r['timestamp'])}_{farmer_id}.jpg"
        try:
            file_bytes = base64.b64decode(image_b64)
            image_url = upload_image_to_supabase(filename, file_bytes)
            if not image_url:
                return {"error": "image upload failed"}, 500
        except Exception as e:
            return {"error": "image upload failed", "detail": str(e)}, 500
    
    # Store detections as JSON
    append_record(timestamp, farmer_id, detections, image_url, device_id=device_id)
    
    return {
        "status": "ok",
        "farmer_id": farmer_id,
        "device_id": device_id,
        "image_url": image_url,
        "detections": detections
    }, 200

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
