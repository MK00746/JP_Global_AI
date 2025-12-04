# app.py - JP Global InsectDetect with Professional Sidebar Navigation
import os, base64, sqlite3, uuid
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
            # Filter by specific device_id
            res = supabase.table("insect_records").select("*").eq("device_id", str(device_id)).order("timestamp", desc=True).execute()
        elif farmer_id:
            # Filter by farmer_id
            res = supabase.table("insect_records").select("*").eq("farmer_id", farmer_id).order("timestamp", desc=True).execute()
        else:
            # Get all records
            res = supabase.table("insect_records").select("*").order("timestamp", desc=True).execute()
        return res.data or []
    except:
        return []

def append_record(timestamp, farmer_id, insect, count, image_url, device_id=None):
    """Append record to Supabase with optional device_id"""
    try:
        record = {
            "timestamp": timestamp,
            "farmer_id": farmer_id,
            "insect": insect,
            "count": count,
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
            if filename.endswith(('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')):
                image_url = supabase.storage.from_(bucket).get_public_url(f"insects/{filename}")
                image_list.append({
                    'filename': filename,
                    'url': image_url
                })
        return image_list
    except Exception as e:
        print(f"Error listing images: {e}")
        return []
    
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
    
    if len(records) > 0:
        df = pd.DataFrame(records)
        df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
        total_insects = int(df["count"].sum())
        insect_summary = df.groupby("insect")["count"].sum().reset_index().to_dict(orient="records")
    else:
        total_insects = 0
        insect_summary = []
    
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
    
    if len(records) > 0:
        df = pd.DataFrame(records)
        df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
        summary = df.groupby("insect")["count"].sum().reset_index().to_dict(orient="records")
    else:
        summary = []
    
    from html_templates import ADMIN_DEVICE_ANALYTICS_HTML
    return render_template_string(ADMIN_DEVICE_ANALYTICS_HTML,
                                   username=user['username'],
                                   device=device,
                                   records=records,
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
    
    from html_templates import ADMIN_DATASET_HTML
    return render_template_string(ADMIN_DATASET_HTML,
                                   username=user['username'],
                                   records=records,
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
    
    # ADD THIS LINE - Get all images from Supabase
    available_images = list_images_from_supabase()
    
    from html_templates import ADMIN_IMAGES_HTML
    return render_template_string(ADMIN_IMAGES_HTML,
                                   username=user['username'],
                                   records=records_with_images,
                                   farmers=farmers,
                                   selected_farmer=selected_farmer,
                                   available_images=available_images)  # ADD THIS

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


# ADD THIS NEW ROUTE HERE
@app.route("/admin/create_record_for_image", methods=["POST"])
def admin_create_record_for_image():
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for("login"))
    
    image_url = request.form.get("image_url")
    farmer_id = request.form.get("farmer_id")
    insect = request.form.get("insect", "unknown")
    count = int(request.form.get("count", 1))
    
    if not image_url or not farmer_id:
        flash("Image URL and Farmer ID are required", "danger")
        return redirect(url_for("admin_images"))
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    append_record(timestamp, farmer_id, insect, count, image_url)
    
    flash(f"Record created successfully for {insect}", "success")
    return redirect(url_for("admin_images"))



# ==================== FARMER ROUTES ====================
@app.route("/farmer/overview")
def farmer_overview():
    user = current_user()
    if not user or user['role'] != 'farmer':
        return redirect(url_for("login"))
    
    records = load_records(farmer_id=user['farmer_id'])
    
    if len(records) > 0:
        df = pd.DataFrame(records)
        df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
        
        # Find insect with highest count
        insect_totals = df.groupby("insect")["count"].sum()
        top_insect = insect_totals.idxmax() if len(insect_totals) > 0 else "N/A"
        top_count = int(insect_totals.max()) if len(insect_totals) > 0 else 0
        
        total_count = int(df["count"].sum())
        insect_summary = df.groupby("insect")["count"].sum().reset_index().to_dict(orient="records")
    else:
        top_insect = "N/A"
        top_count = 0
        total_count = 0
        insect_summary = []
    
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
    
    from html_templates import FARMER_ANALYSIS_HTML
    return render_template_string(FARMER_ANALYSIS_HTML,
                                   username=user['username'],
                                   farmer_id=user['farmer_id'],
                                   records=records)

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
    
    from html_templates import FARMER_DATASET_HTML
    return render_template_string(FARMER_DATASET_HTML,
                                   username=user['username'],
                                   records=records,
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
    
    from html_templates import FARMER_IMAGES_HTML
    return render_template_string(FARMER_IMAGES_HTML,
                                   username=user['username'],
                                   records=records_with_images,
                                   devices=devices,
                                   selected_device=selected_device)

# ==================== API ROUTES ====================
@app.route("/api/analysis_data")
def api_analysis_data():
    """API endpoint for fetching filtered analysis data"""
    farmer_id = request.args.get("farmer_id")
    days = int(request.args.get("days", 7))
    
    if not farmer_id:
        return jsonify({"error": "farmer_id required"}), 400
    
    records = load_records(farmer_id=farmer_id)
    
    if len(records) == 0:
        return jsonify({"labels": [], "bar_data": [], "line_data": []})
    
    df = pd.DataFrame(records)
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    
    # Filter by date range
    cutoff_date = datetime.now() - timedelta(days=days)
    df_filtered = df[df["timestamp"] >= cutoff_date]
    
    # Five insects
    insects = ["whiteflies", "aphids", "thrips", "beetle", "fungus gnats"]
    
    # Bar chart data (total per insect)
    bar_data = []
    for insect in insects:
        count = int(df_filtered[df_filtered["insect"] == insect]["count"].sum())
        bar_data.append(count)
    
    # Line chart data (daily trends)
    df_filtered["date"] = df_filtered["timestamp"].dt.date
    daily_data = df_filtered.groupby(["date", "insect"])["count"].sum().reset_index()
    
    # Get last N days dates
    dates = pd.date_range(end=datetime.now(), periods=min(days, 30), freq='D')
    date_labels = [d.strftime("%Y-%m-%d") for d in dates]
    
    # Create line data for each insect
    line_datasets = []
    colors = [
        "rgba(255, 127, 80, 0.8)",   # whiteflies - orange
        "rgba(64, 156, 255, 0.8)",   # aphids - blue
        "rgba(76, 217, 100, 0.8)",   # thrips - green
        "rgba(175, 82, 222, 0.8)",   # beetle - purple
        "rgba(255, 204, 0, 0.8)"     # fungus gnats - gold
    ]
    
    for idx, insect in enumerate(insects):
        insect_data = []
        for date_str in date_labels:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            matching = daily_data[(daily_data["date"] == date_obj) & (daily_data["insect"] == insect)]
            count = int(matching["count"].sum()) if len(matching) > 0 else 0
            insect_data.append(count)
        
        line_datasets.append({
            "label": insect.title(),
            "data": insect_data,
            "borderColor": colors[idx],
            "backgroundColor": colors[idx].replace("0.8", "0.2"),
            "tension": 0.4
        })
    
    return jsonify({
        "labels": insects,
        "bar_data": bar_data,
        "line_labels": date_labels,
        "line_datasets": line_datasets
    })

@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json(silent=True)
    
    # Case 1: JSON body
    if data:
        farmer_id = data.get("farmer_id", "unknown")
        insect = data.get("insect", "unknown")
        count = int(data.get("count", 0))
        image_b64 = data.get("image_b64")
        
        if not image_b64:
            return {"error": "No image data received"}, 400
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{farmer_id}.jpg"
        
        try:
            file_bytes = base64.b64decode(image_b64)
            image_url = upload_image_to_supabase(filename, file_bytes)
            if not image_url:
                return {"error": "Image upload failed"}, 500
        except Exception as e:
            return {"error": "image upload failed", "detail": str(e)}, 500
        
        append_record(timestamp, farmer_id, insect, count, image_url)
        
        return {
            "status": "ok",
            "farmer_id": farmer_id,
            "image_url": image_url,
            "insect": insect,
            "count": count
        }, 200
    
    # Case 2: Form upload
    if 'image' in request.files:
        f = request.files['image']
        farmer_id = request.form.get("farmer_id", "unknown")
        insect = request.form.get("insect", "unknown")
        count = int(request.form.get("count", 0))
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{farmer_id}.jpg"
        file_bytes = f.read()
        
        image_url = upload_image_to_supabase(filename, file_bytes)
        if not image_url:
            return {"error": "Image upload failed"}, 500
            
        append_record(timestamp, farmer_id, insect, count, image_url)
        return {"status": "ok", "image_url": image_url}, 200
    
    return {"error": "Invalid upload format"}, 400

@app.route('/api/upload_result', methods=['POST'])
def upload_result():
    """Device upload endpoint with device key authentication"""
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
    
    insect = data.get("insect", "unknown")
    try:
        count = int(data.get("count", 0))
    except:
        count = 0
    
    image_b64 = data.get("image_base64") or data.get("image_b64")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    image_url = ""
    if image_b64:
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{farmer_id}.jpg"
        try:
            file_bytes = base64.b64decode(image_b64)
            image_url = upload_image_to_supabase(filename, file_bytes)
        except Exception as e:
            return {"error": "image upload failed", "detail": str(e)}, 500
    
    append_record(timestamp, farmer_id, insect, count, image_url, device_id=device_id)
    
    return {
        "status": "ok",
        "farmer_id": farmer_id,
        "device_id": device_id,
        "image_url": image_url,
        "insect": insect,
        "count": count
    }, 200

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
