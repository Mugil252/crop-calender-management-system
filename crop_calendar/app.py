from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import hashlib
import os
from datetime import datetime, date, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'crop_calendar_secret_key_2024'

DATABASE = 'database.db'

# ─────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
# DATABASE INITIALIZATION
# ─────────────────────────────────────────────

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        mobile TEXT NOT NULL UNIQUE,
        location TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Crops master table
    c.execute('''CREATE TABLE IF NOT EXISTS crops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crop_name TEXT NOT NULL,
        variety TEXT NOT NULL,
        season TEXT NOT NULL,
        duration_days INTEGER NOT NULL,
        soil_type TEXT,
        water_requirement TEXT
    )''')

    # Crop activities master table
    c.execute('''CREATE TABLE IF NOT EXISTS crop_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crop_id INTEGER NOT NULL,
        activity_name TEXT NOT NULL,
        day_after_sowing INTEGER NOT NULL,
        description TEXT,
        FOREIGN KEY (crop_id) REFERENCES crops(id)
    )''')

    # Farmer's crops table
    c.execute('''CREATE TABLE IF NOT EXISTS farmer_crops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        crop_id INTEGER NOT NULL,
        sowing_date DATE NOT NULL,
        expected_harvest_date DATE,
        status TEXT DEFAULT 'active',
        field_area REAL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (crop_id) REFERENCES crops(id)
    )''')

    # Activity tracking table
    c.execute('''CREATE TABLE IF NOT EXISTS activity_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_crop_id INTEGER NOT NULL,
        activity_id INTEGER NOT NULL,
        scheduled_date DATE NOT NULL,
        status TEXT DEFAULT 'upcoming',
        completed_date DATE,
        notes TEXT,
        FOREIGN KEY (farmer_crop_id) REFERENCES farmer_crops(id),
        FOREIGN KEY (activity_id) REFERENCES crop_activities(id)
    )''')

    conn.commit()

    # Insert sample crops if empty
    c.execute('SELECT COUNT(*) FROM crops')
    if c.fetchone()[0] == 0:
        insert_sample_data(c)
        conn.commit()

    conn.close()

def insert_sample_data(c):
    """Insert all 10 crops with varieties, seasons and activity schedules."""

    crops_data = [
        # (crop_name, variety, season, duration_days, soil_type, water_requirement)
        ('Rice/Paddy', 'IR-64', 'Kharif', 120, 'Clay Loam', 'High'),
        ('Rice/Paddy', 'Sona Masuri', 'Rabi', 130, 'Clay Loam', 'High'),
        ('Maize', 'Hybrid DHM-117', 'Kharif', 90, 'Sandy Loam', 'Medium'),
        ('Maize', 'KPMH-17', 'Rabi', 100, 'Sandy Loam', 'Medium'),
        ('Groundnut', 'TMV-7', 'Kharif', 110, 'Sandy Loam', 'Medium'),
        ('Groundnut', 'K-6', 'Rabi', 120, 'Sandy Loam', 'Medium'),
        ('Cotton', 'Bt Cotton', 'Kharif', 180, 'Black Cotton', 'Medium'),
        ('Cotton', 'MCU-5', 'Kharif', 190, 'Black Cotton', 'Medium'),
        ('Chilli', 'K-1', 'Kharif', 150, 'Red Loam', 'Medium'),
        ('Chilli', 'Guntur Sannam', 'Rabi', 160, 'Red Loam', 'Medium'),
        ('Tomato', 'Arka Rakshak', 'Rabi', 120, 'Sandy Loam', 'Medium'),
        ('Tomato', 'PKM-1', 'Kharif', 110, 'Sandy Loam', 'Medium'),
        ('Brinjal', 'CO-1', 'All Season', 140, 'Loam', 'Medium'),
        ('Brinjal', 'Arka Nidhi', 'Kharif', 130, 'Loam', 'Medium'),
        ('Onion', 'Agrifound Dark Red', 'Rabi', 120, 'Sandy Loam', 'Low'),
        ('Onion', 'N-53', 'Kharif', 110, 'Sandy Loam', 'Low'),
        ('Ragi', 'GPU-28', 'Kharif', 100, 'Red Laterite', 'Low'),
        ('Ragi', 'MR-6', 'Rabi', 110, 'Red Laterite', 'Low'),
        ('Sugarcane', 'Co-86032', 'Annual', 360, 'Deep Loam', 'High'),
        ('Sugarcane', 'Co-0238', 'Annual', 365, 'Deep Loam', 'High'),
    ]

    c.executemany(
        'INSERT INTO crops (crop_name, variety, season, duration_days, soil_type, water_requirement) VALUES (?,?,?,?,?,?)',
        crops_data
    )

    # Fetch inserted crop IDs grouped by crop_name
    c.execute('SELECT id, crop_name, variety FROM crops')
    all_crops = c.fetchall()

    # Build a mapping: (crop_name, variety) -> id
    crop_map = {(r[1], r[2]): r[0] for r in all_crops}

    # Activity schedules per crop type
    activity_templates = {
        'Rice/Paddy': [
            ('Land Preparation', 0, 'Plough and level the field. Prepare nursery bed for seedling raising.'),
            ('Nursery Preparation', 0, 'Prepare nursery bed; sow pre-germinated seeds at 25–30 kg/acre.'),
            ('Transplanting', 21, 'Transplant 21-day-old seedlings at 20×15 cm spacing.'),
            ('First Irrigation', 1, 'Flood irrigate the field immediately after transplanting.'),
            ('First Fertilizer (Basal)', 21, 'Apply basal dose of NPK (40-20-20 kg/acre) at transplanting.'),
            ('First Weeding', 25, 'Manual or chemical weeding to remove early weeds.'),
            ('Second Irrigation', 10, 'Maintain 5 cm water level in the field.'),
            ('Tillering Fertilizer', 35, 'Apply urea @ 20 kg/acre for tillering stage.'),
            ('Pest Monitoring', 40, 'Monitor for stem borer, leaf folder and BPH insects.'),
            ('Second Weeding', 45, 'Apply weedicide or manual weeding for second flush.'),
            ('Panicle Initiation Fertilizer', 55, 'Apply potash @ 20 kg/acre at panicle initiation.'),
            ('Disease Monitoring', 60, 'Check for blast, sheath blight and brown spot diseases.'),
            ('Third Irrigation', 70, 'Maintain water level; drain 10 days before harvest.'),
            ('Harvesting', 110, 'Harvest when 80% grains turn golden yellow. Thresh and dry.'),
        ],
        'Maize': [
            ('Land Preparation', 0, 'Deep plough and prepare fine seedbed. Apply FYM 5 t/acre.'),
            ('Sowing', 0, 'Sow seeds at 60×20 cm spacing; seed rate 8–10 kg/acre.'),
            ('First Irrigation', 3, 'Light irrigation immediately after sowing.'),
            ('Germination Check', 7, 'Check germination and gap filling within 7 days of sowing.'),
            ('First Fertilizer (Basal)', 0, 'Apply NPK 40-20-20 kg/acre as basal dose.'),
            ('First Weeding', 15, 'Manual weeding or apply atrazine herbicide.'),
            ('Second Irrigation', 20, 'Irrigate at knee-high stage.'),
            ('Top Dressing Fertilizer', 30, 'Apply urea 20 kg/acre at knee-high stage.'),
            ('Pest Monitoring (FAW)', 35, 'Monitor for Fall Armyworm in whorls; apply recommended insecticide.'),
            ('Second Weeding', 40, 'Earthing up and second weeding operation.'),
            ('Tasseling Fertilizer', 50, 'Apply potash 20 kg/acre at tasseling stage.'),
            ('Disease Monitoring', 55, 'Check for turcicum blight and maydis leaf blight.'),
            ('Third Irrigation', 60, 'Critical irrigation at tasseling and silking stage.'),
            ('Harvesting', 85, 'Harvest when husks turn brown and grains are hard. Dry to 12% moisture.'),
        ],
        'Groundnut': [
            ('Land Preparation', 0, 'Plough 2–3 times and level the field. Apply gypsum 200 kg/acre.'),
            ('Seed Treatment', 0, 'Treat seeds with Rhizobium and PSB culture before sowing.'),
            ('Sowing', 0, 'Sow at 30×10 cm spacing; seed rate 70–80 kg/acre (bold seeded).'),
            ('First Irrigation', 3, 'Pre-sowing irrigation or light irrigation after sowing.'),
            ('First Weeding', 15, 'Manual weeding or apply pendimethalin herbicide.'),
            ('First Fertilizer', 0, 'Apply NPK 10-20-20 kg/acre as basal dose.'),
            ('Second Irrigation', 25, 'Irrigate at pegging stage (25–30 DAS).'),
            ('Earthing Up', 30, 'Earth up to facilitate peg penetration into soil.'),
            ('Gypsum Application', 40, 'Apply gypsum 200 kg/acre at peg formation stage.'),
            ('Pest Monitoring (Aphid)', 45, 'Monitor for aphids, thrips and leaf miner; spray if needed.'),
            ('Disease Monitoring', 50, 'Check for tikka leaf spot and rust diseases.'),
            ('Third Irrigation', 60, 'Irrigate at pod development stage.'),
            ('Fourth Irrigation', 80, 'Last irrigation; stop 10 days before harvest.'),
            ('Harvesting', 105, 'Harvest when leaves turn yellow. Dry pods in sun for 3–4 days.'),
        ],
        'Cotton': [
            ('Land Preparation', 0, 'Deep plough and prepare ridges and furrows at 90 cm spacing.'),
            ('Sowing', 0, 'Sow Bt cotton seeds at 90×60 cm; seed rate 1.5 kg/acre.'),
            ('First Irrigation', 5, 'Pre-sowing irrigation; sow in furrows.'),
            ('Gap Filling', 10, 'Fill gaps within 10 days of germination.'),
            ('First Weeding', 20, 'Manual intercultivation; apply herbicide if required.'),
            ('Basal Fertilizer', 0, 'Apply FYM 4 t/acre and NPK 32-16-16 kg/acre at sowing.'),
            ('Second Irrigation', 25, 'Irrigate at squaring stage.'),
            ('First Top Dressing', 30, 'Apply urea 25 kg/acre at first top dressing.'),
            ('Second Weeding', 45, 'Second intercultivation and earthing up.'),
            ('Bollworm Monitoring', 50, 'Monitor for bollworms; set pheromone traps.'),
            ('Second Top Dressing', 60, 'Apply potash 25 kg/acre at boll development.'),
            ('Disease Monitoring', 70, 'Check for alternaria blight and grey mildew.'),
            ('Third Irrigation', 80, 'Irrigate at boll opening stage.'),
            ('Plant Growth Regulator', 90, 'Apply Mepiquat chloride 5 g/litre at square stage.'),
            ('Defoliation', 160, 'Apply defoliant 2 weeks before final harvest.'),
            ('Harvesting', 175, 'Pick mature open bolls. Do 3–4 pickings at 2-week intervals.'),
        ],
        'Chilli': [
            ('Nursery Preparation', 0, 'Prepare raised nursery beds; treat seeds with trichoderma.'),
            ('Nursery Sowing', 0, 'Sow chilli seeds in nursery @ 100 g per 10 sq.m bed.'),
            ('Transplanting', 35, 'Transplant 35-day-old seedlings at 60×45 cm spacing.'),
            ('First Irrigation', 1, 'Irrigate immediately after transplanting.'),
            ('Basal Fertilizer', 35, 'Apply NPK 20-24-24 kg/acre at transplanting.'),
            ('First Weeding', 20, 'Manual weeding in nursery and transplanted field.'),
            ('Second Irrigation', 10, 'Irrigate every 7–10 days depending on weather.'),
            ('First Top Dressing', 45, 'Apply urea 20 kg/acre 10 days after transplanting.'),
            ('Pest Monitoring (Thrips)', 50, 'Monitor thrips and mites; spray systemic insecticide.'),
            ('Second Weeding', 55, 'Manual or chemical weeding.'),
            ('Disease Monitoring (Wilt)', 60, 'Check for Phytophthora wilt; improve drainage.'),
            ('Second Top Dressing', 70, 'Apply potash 20 kg/acre at fruiting stage.'),
            ('Third Irrigation', 75, 'Critical irrigation at flowering and fruit set.'),
            ('Fruit Borer Monitoring', 90, 'Monitor for fruit borer; apply spinosad if needed.'),
            ('Harvesting', 140, 'Harvest red ripe chillies. Dry to 10% moisture for marketing.'),
        ],
        'Tomato': [
            ('Nursery Preparation', 0, 'Prepare nursery beds with coco peat and vermicompost.'),
            ('Nursery Sowing', 0, 'Sow tomato seeds in pro-trays; 100 g seed per acre.'),
            ('Transplanting', 25, 'Transplant 25-day-old seedlings at 60×45 cm spacing.'),
            ('First Irrigation', 1, 'Drip irrigate immediately after transplanting.'),
            ('Staking', 30, 'Provide bamboo stakes and tie the plants.'),
            ('Basal Fertilizer', 25, 'Apply NPK 50-50-50 kg/acre at planting.'),
            ('First Top Dressing', 40, 'Apply urea 20 kg/acre at vegetative stage.'),
            ('First Weeding', 20, 'Remove weeds manually in the nursery beds.'),
            ('Pest Monitoring', 45, 'Monitor for whitefly, thrips and fruit borer.'),
            ('Disease Monitoring', 50, 'Check for early blight, late blight and leaf curl virus.'),
            ('Second Top Dressing', 60, 'Apply calcium nitrate 15 kg/acre at fruiting.'),
            ('Second Irrigation', 30, 'Irrigate at regular intervals; avoid water stress at flowering.'),
            ('Topping/Pruning', 55, 'Remove suckers and top the plant at 5–6 clusters.'),
            ('Harvesting', 90, 'Harvest when fruits turn light red. Pick every 3 days.'),
        ],
        'Brinjal': [
            ('Nursery Preparation', 0, 'Prepare raised nursery beds; apply well decomposed FYM.'),
            ('Nursery Sowing', 0, 'Sow brinjal seeds in nursery @ 200 g/acre.'),
            ('Transplanting', 30, 'Transplant 30-day-old seedlings at 60×60 cm spacing.'),
            ('First Irrigation', 1, 'Irrigate immediately after transplanting.'),
            ('Basal Fertilizer', 30, 'Apply NPK 20-24-24 kg/acre at transplanting.'),
            ('First Weeding', 20, 'Manual weeding at 15–20 days after transplanting.'),
            ('First Top Dressing', 45, 'Apply urea 20 kg/acre at 15 days after transplanting.'),
            ('Pest Monitoring (Shoot Borer)', 50, 'Monitor shoot and fruit borer; use pheromone traps.'),
            ('Disease Monitoring', 55, 'Check for little leaf virus and Phomopsis blight.'),
            ('Second Irrigation', 30, 'Irrigate every 7 days in dry season.'),
            ('Second Top Dressing', 70, 'Apply potash 20 kg/acre at fruiting stage.'),
            ('Second Weeding', 60, 'Second manual weeding and earthing up.'),
            ('Harvesting', 90, 'Harvest tender fruits at 2–3 day intervals for market.'),
        ],
        'Onion': [
            ('Nursery Preparation', 0, 'Prepare raised nursery beds 1 m wide; sterilize soil.'),
            ('Nursery Sowing', 0, 'Sow onion seeds in nursery @ 4–5 kg/acre.'),
            ('Transplanting', 40, 'Transplant 40-day-old seedlings at 15×10 cm spacing.'),
            ('First Irrigation', 1, 'Light irrigation after transplanting.'),
            ('Basal Fertilizer', 40, 'Apply NPK 25-25-25 kg/acre at transplanting.'),
            ('First Weeding', 20, 'Manual weeding 20 days after transplanting.'),
            ('First Top Dressing', 55, 'Apply urea 15 kg/acre at 15 days after transplanting.'),
            ('Pest Monitoring (Thrips)', 60, 'Monitor thrips; spray imidacloprid if infestation severe.'),
            ('Disease Monitoring', 65, 'Check for purple blotch and stemphylium blight.'),
            ('Second Irrigation', 30, 'Irrigate at regular intervals; stop 15 days before harvest.'),
            ('Second Weeding', 70, 'Second manual weeding at bulb initiation stage.'),
            ('Neck Fall Observation', 105, 'Observe when 50% plants show neck fall for harvest timing.'),
            ('Harvesting', 110, 'Harvest when 75% plants show neck fall. Cure in shade 7–10 days.'),
        ],
        'Ragi': [
            ('Land Preparation', 0, 'Plough 2–3 times; prepare fine seedbed with FYM 2 t/acre.'),
            ('Sowing', 0, 'Drill sowing at 22.5×10 cm; seed rate 5 kg/acre.'),
            ('First Irrigation', 5, 'Light irrigation if no rain within 5 days of sowing.'),
            ('Gap Filling', 10, 'Fill gaps and thinning at 10 days; maintain one plant per hill.'),
            ('First Weeding', 15, 'Manual weeding at 15–20 DAS.'),
            ('Basal Fertilizer', 0, 'Apply NPK 20-10-10 kg/acre as basal dose.'),
            ('First Top Dressing', 25, 'Apply urea 15 kg/acre at 25 DAS (tillering stage).'),
            ('Pest Monitoring', 30, 'Monitor for shoot fly and aphids; apply systemic insecticide.'),
            ('Disease Monitoring', 40, 'Check for blast disease; spray carbendazim if seen.'),
            ('Second Irrigation', 45, 'Irrigate at panicle initiation stage.'),
            ('Second Top Dressing', 50, 'Apply potash 10 kg/acre at panicle initiation.'),
            ('Third Irrigation', 65, 'Irrigate at grain filling stage.'),
            ('Harvesting', 95, 'Harvest when grain turns dark brown. Thresh and dry to 12% moisture.'),
        ],
        'Sugarcane': [
            ('Land Preparation', 0, 'Deep ploughing and subsoiling; prepare furrows at 90 cm spacing.'),
            ('Planting (Sets)', 0, 'Plant 3-budded setts in furrows; seed rate 2.5 t/acre.'),
            ('First Irrigation', 3, 'Furrow irrigation immediately after planting.'),
            ('Germination Check', 20, 'Check germination; gap fill with fresh setts.'),
            ('Trash Mulching', 30, 'Mulch with sugarcane trash to conserve moisture.'),
            ('Basal Fertilizer', 0, 'Apply FYM 8 t/acre and NPK 50-50-50 kg/acre at planting.'),
            ('First Top Dressing', 45, 'Apply urea 50 kg/acre at 45 days after planting.'),
            ('First Weeding', 30, 'Manual or chemical weeding with atrazine herbicide.'),
            ('Propping', 90, 'Prop the plants to prevent lodging; tie in bundles.'),
            ('Second Top Dressing', 90, 'Apply urea 50 kg/acre and potash 25 kg/acre.'),
            ('Pest Monitoring (Borer)', 100, 'Monitor for internode borer and pyrilla; set pheromone traps.'),
            ('Disease Monitoring', 120, 'Check for red rot and smut diseases; rogue infected clumps.'),
            ('Detrashing', 150, 'Remove dried leaves (trash) from the base of the plant.'),
            ('Second Weeding', 60, 'Second manual weeding and earthing up.'),
            ('Third Top Dressing', 180, 'Apply micronutrient mixture at grand growth stage.'),
            ('Harvesting', 350, 'Harvest when brix reading is 18–20%. Cut at ground level.'),
        ],
    }

    # Map crop_name to their activity templates
    for crop_name, activities in activity_templates.items():
        # Get all crop IDs for this crop_name
        matching = [(v, k) for k, v in crop_map.items() if k[0] == crop_name]
        for crop_id, _ in matching:
            for act in activities:
                c.execute(
                    'INSERT INTO crop_activities (crop_id, activity_name, day_after_sowing, description) VALUES (?,?,?,?)',
                    (crop_id, act[0], act[1], act[2])
                )

    # Insert a demo farmer account
    c.execute(
        'INSERT OR IGNORE INTO users (name, mobile, location, password_hash) VALUES (?,?,?,?)',
        ('Demo Farmer', '9876543210', 'Hyderabad, Telangana', hash_password('farmer123'))
    )


# ─────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────

def calculate_activity_status(scheduled_date_str):
    today = date.today()
    try:
        scheduled = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
    except Exception:
        return 'upcoming'

    diff = (scheduled - today).days
    if diff < 0:
        return 'overdue'
    elif diff == 0:
        return 'due_today'
    elif diff <= 7:
        return 'upcoming'
    else:
        return 'upcoming'

def get_days_remaining(scheduled_date_str):
    today = date.today()
    try:
        scheduled = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
        return (scheduled - today).days
    except Exception:
        return None

def get_user_stats(user_id):
    conn = get_db()
    c = conn.cursor()
    today = date.today().strftime('%Y-%m-%d')

    # Active crops
    c.execute("SELECT COUNT(*) FROM farmer_crops WHERE user_id=? AND status='active'", (user_id,))
    active_crops = c.fetchone()[0]

    # Activity counts
    c.execute('''SELECT at.status, COUNT(*) FROM activity_tracking at
                 JOIN farmer_crops fc ON at.farmer_crop_id=fc.id
                 WHERE fc.user_id=? GROUP BY at.status''', (user_id,))
    status_counts = dict(c.fetchall())

    # Recalculate live statuses
    c.execute('''SELECT at.id, at.scheduled_date, at.status FROM activity_tracking at
                 JOIN farmer_crops fc ON at.farmer_crop_id=fc.id
                 WHERE fc.user_id=? AND at.status NOT IN ('completed','delayed')''', (user_id,))
    pending_acts = c.fetchall()

    overdue = 0
    due_today = 0
    upcoming = 0
    for act in pending_acts:
        days = get_days_remaining(act['scheduled_date'])
        if days is None:
            continue
        if days < 0:
            overdue += 1
        elif days == 0:
            due_today += 1
        else:
            upcoming += 1

    completed = status_counts.get('completed', 0)
    delayed = status_counts.get('delayed', 0)

    conn.close()
    return {
        'active_crops': active_crops,
        'completed': completed,
        'upcoming': upcoming,
        'due_today': due_today,
        'overdue': overdue,
        'delayed': delayed,
    }

def get_reminders(user_id):
    conn = get_db()
    c = conn.cursor()
    today = date.today()
    tomorrow = today + timedelta(days=1)

    c.execute('''SELECT at.id, ca.activity_name, cr.crop_name, at.scheduled_date
                 FROM activity_tracking at
                 JOIN farmer_crops fc ON at.farmer_crop_id=fc.id
                 JOIN crop_activities ca ON at.activity_id=ca.id
                 JOIN crops cr ON fc.crop_id=cr.id
                 WHERE fc.user_id=? AND at.status NOT IN ('completed','delayed')
                 ORDER BY at.scheduled_date ASC LIMIT 20''', (user_id,))
    rows = c.fetchall()
    conn.close()

    reminders = []
    for row in rows:
        days = get_days_remaining(row['scheduled_date'])
        if days is None:
            continue
        if days < 0:
            reminders.append({'type': 'danger', 'msg': f"⚠ {row['crop_name']} – {row['activity_name']} is overdue by {abs(days)} day(s)!"})
        elif days == 0:
            reminders.append({'type': 'warning', 'msg': f"📅 {row['crop_name']} – {row['activity_name']} is due TODAY!"})
        elif days == 1:
            reminders.append({'type': 'info', 'msg': f"🔔 {row['crop_name']} – {row['activity_name']} is scheduled tomorrow."})
        elif days <= 3:
            reminders.append({'type': 'info', 'msg': f"📌 {row['crop_name']} – {row['activity_name']} is in {days} days."})

    return reminders[:10]


# ─────────────────────────────────────────────
# ROUTES – AUTH
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form.get('mobile', '').strip()
        password = request.form.get('password', '').strip()
        if not mobile or not password:
            flash('Please fill all fields.', 'danger')
            return render_template('login.html')
        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE mobile=? AND password_hash=?',
            (mobile, hash_password(password))
        ).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid mobile number or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        location = request.form.get('location', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()

        if not all([name, mobile, location, password, confirm]):
            flash('Please fill all fields.', 'danger')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        if len(mobile) != 10 or not mobile.isdigit():
            flash('Enter a valid 10-digit mobile number.', 'danger')
            return render_template('register.html')

        conn = get_db()
        try:
            conn.execute(
                'INSERT INTO users (name, mobile, location, password_hash) VALUES (?,?,?,?)',
                (name, mobile, location, hash_password(password))
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Mobile number already registered.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# ROUTES – DASHBOARD
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    stats = get_user_stats(user_id)
    reminders = get_reminders(user_id)
    today = date.today()

    conn = get_db()
    # Upcoming activities in next 7 days
    week_end = (today + timedelta(days=7)).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')

    upcoming_acts = conn.execute('''
        SELECT ca.activity_name, cr.crop_name, at.scheduled_date, at.status, at.id
        FROM activity_tracking at
        JOIN farmer_crops fc ON at.farmer_crop_id=fc.id
        JOIN crop_activities ca ON at.activity_id=ca.id
        JOIN crops cr ON fc.crop_id=cr.id
        WHERE fc.user_id=? AND at.scheduled_date BETWEEN ? AND ?
        AND at.status NOT IN ('completed','delayed')
        ORDER BY at.scheduled_date ASC LIMIT 10
    ''', (user_id, today_str, week_end)).fetchall()

    # Active crops with progress
    active_crops = conn.execute('''
        SELECT fc.id, cr.crop_name, cr.variety, fc.sowing_date, fc.expected_harvest_date,
               cr.duration_days, fc.status
        FROM farmer_crops fc
        JOIN crops cr ON fc.crop_id=cr.id
        WHERE fc.user_id=? AND fc.status='active'
        ORDER BY fc.created_at DESC LIMIT 5
    ''', (user_id,)).fetchall()

    crop_progress = []
    for crop in active_crops:
        total = conn.execute(
            'SELECT COUNT(*) FROM activity_tracking WHERE farmer_crop_id=?', (crop['id'],)
        ).fetchone()[0]
        done = conn.execute(
            "SELECT COUNT(*) FROM activity_tracking WHERE farmer_crop_id=? AND status='completed'", (crop['id'],)
        ).fetchone()[0]
        pct = round((done / total * 100) if total > 0 else 0, 1)
        days_since = (today - datetime.strptime(crop['sowing_date'], '%Y-%m-%d').date()).days
        crop_progress.append({
            'id': crop['id'],
            'crop_name': crop['crop_name'],
            'variety': crop['variety'],
            'sowing_date': crop['sowing_date'],
            'expected_harvest': crop['expected_harvest_date'],
            'progress': pct,
            'days_since': days_since,
            'duration': crop['duration_days'],
        })

    conn.close()
    return render_template('dashboard.html',
        stats=stats, reminders=reminders,
        upcoming_acts=upcoming_acts, crop_progress=crop_progress,
        today=today.strftime('%B %d, %Y')
    )


# ─────────────────────────────────────────────
# ROUTES – CROPS
# ─────────────────────────────────────────────

@app.route('/crops')
@login_required
def crops():
    user_id = session['user_id']
    conn = get_db()
    farmer_crops = conn.execute('''
        SELECT fc.id, cr.crop_name, cr.variety, cr.season, fc.sowing_date,
               fc.expected_harvest_date, fc.status, fc.field_area
        FROM farmer_crops fc
        JOIN crops cr ON fc.crop_id=cr.id
        WHERE fc.user_id=?
        ORDER BY fc.created_at DESC
    ''', (user_id,)).fetchall()

    today = date.today()
    crops_data = []
    for fc in farmer_crops:
        total = conn.execute(
            'SELECT COUNT(*) FROM activity_tracking WHERE farmer_crop_id=?', (fc['id'],)
        ).fetchone()[0]
        done = conn.execute(
            "SELECT COUNT(*) FROM activity_tracking WHERE farmer_crop_id=? AND status='completed'", (fc['id'],)
        ).fetchone()[0]
        pct = round((done / total * 100) if total > 0 else 0, 1)
        crops_data.append({**dict(fc), 'progress': pct, 'completed': done, 'total': total})

    conn.close()
    return render_template('crops.html', crops=crops_data, today=today)

@app.route('/add_crop', methods=['GET', 'POST'])
@login_required
def add_crop():
    conn = get_db()
    all_crops = conn.execute('SELECT DISTINCT crop_name FROM crops ORDER BY crop_name').fetchall()

    if request.method == 'POST':
        user_id = session['user_id']
        crop_id = request.form.get('crop_id')
        sowing_date_str = request.form.get('sowing_date')
        field_area = request.form.get('field_area', 0)
        notes = request.form.get('notes', '')

        if not crop_id or not sowing_date_str:
            flash('Please select a crop and enter sowing date.', 'danger')
            conn.close()
            return render_template('add_crop.html', all_crops=all_crops)

        sowing_date = datetime.strptime(sowing_date_str, '%Y-%m-%d').date()
        crop_info = conn.execute('SELECT * FROM crops WHERE id=?', (crop_id,)).fetchone()
        harvest_date = sowing_date + timedelta(days=crop_info['duration_days'])

        # Insert farmer crop
        cur = conn.execute(
            'INSERT INTO farmer_crops (user_id, crop_id, sowing_date, expected_harvest_date, field_area, notes) VALUES (?,?,?,?,?,?)',
            (user_id, crop_id, sowing_date_str, harvest_date.strftime('%Y-%m-%d'), field_area, notes)
        )
        farmer_crop_id = cur.lastrowid

        # Auto-generate activity schedule
        activities = conn.execute(
            'SELECT * FROM crop_activities WHERE crop_id=?', (crop_id,)
        ).fetchall()

        for act in activities:
            scheduled = sowing_date + timedelta(days=act['day_after_sowing'])
            conn.execute(
                'INSERT INTO activity_tracking (farmer_crop_id, activity_id, scheduled_date) VALUES (?,?,?)',
                (farmer_crop_id, act['id'], scheduled.strftime('%Y-%m-%d'))
            )

        conn.commit()
        conn.close()
        flash('Crop added successfully! Activity calendar generated.', 'success')
        return redirect(url_for('crops'))

    conn.close()
    return render_template('add_crop.html', all_crops=all_crops)

@app.route('/api/crop_varieties/<crop_name>')
@login_required
def crop_varieties(crop_name):
    conn = get_db()
    varieties = conn.execute(
        'SELECT id, variety, season, duration_days, soil_type, water_requirement FROM crops WHERE crop_name=?',
        (crop_name,)
    ).fetchall()
    conn.close()
    return jsonify([dict(v) for v in varieties])

@app.route('/delete_crop/<int:fc_id>', methods=['POST'])
@login_required
def delete_crop(fc_id):
    user_id = session['user_id']
    conn = get_db()
    fc = conn.execute('SELECT * FROM farmer_crops WHERE id=? AND user_id=?', (fc_id, user_id)).fetchone()
    if fc:
        conn.execute('DELETE FROM activity_tracking WHERE farmer_crop_id=?', (fc_id,))
        conn.execute('DELETE FROM farmer_crops WHERE id=?', (fc_id,))
        conn.commit()
        flash('Crop removed.', 'success')
    conn.close()
    return redirect(url_for('crops'))


# ─────────────────────────────────────────────
# ROUTES – CALENDAR
# ─────────────────────────────────────────────

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@app.route('/api/calendar_events')
@login_required
def calendar_events():
    user_id = session['user_id']
    conn = get_db()
    rows = conn.execute('''
        SELECT at.id, at.scheduled_date, at.status, at.completed_date,
               ca.activity_name, ca.description,
               cr.crop_name, cr.variety
        FROM activity_tracking at
        JOIN farmer_crops fc ON at.farmer_crop_id=fc.id
        JOIN crop_activities ca ON at.activity_id=ca.id
        JOIN crops cr ON fc.crop_id=cr.id
        WHERE fc.user_id=?
    ''', (user_id,)).fetchall()
    conn.close()

    today = date.today()
    events = []
    color_map = {
        'completed': '#28a745',
        'delayed': '#6c757d',
        'due_today': '#fd7e14',
        'overdue': '#dc3545',
        'upcoming': '#17a2b8',
    }

    for row in rows:
        if row['status'] in ('completed', 'delayed'):
            status = row['status']
        else:
            days = get_days_remaining(row['scheduled_date'])
            if days is None:
                status = 'upcoming'
            elif days < 0:
                status = 'overdue'
            elif days == 0:
                status = 'due_today'
            else:
                status = 'upcoming'

        events.append({
            'id': row['id'],
            'title': f"{row['crop_name']} – {row['activity_name']}",
            'start': row['scheduled_date'],
            'color': color_map.get(status, '#17a2b8'),
            'extendedProps': {
                'crop_name': row['crop_name'],
                'variety': row['variety'],
                'activity_name': row['activity_name'],
                'description': row['description'],
                'status': status,
                'scheduled_date': row['scheduled_date'],
                'completed_date': row['completed_date'],
            }
        })

    return jsonify(events)


# ─────────────────────────────────────────────
# ROUTES – ACTIVITIES
# ─────────────────────────────────────────────

@app.route('/activities')
@login_required
def activities():
    user_id = session['user_id']
    conn = get_db()

    status_filter = request.args.get('status', 'all')
    crop_filter = request.args.get('crop', '')
    search = request.args.get('search', '')

    query = '''
        SELECT at.id, at.scheduled_date, at.status, at.completed_date,
               ca.activity_name, ca.description,
               cr.crop_name, cr.variety, fc.id as fc_id
        FROM activity_tracking at
        JOIN farmer_crops fc ON at.farmer_crop_id=fc.id
        JOIN crop_activities ca ON at.activity_id=ca.id
        JOIN crops cr ON fc.crop_id=cr.id
        WHERE fc.user_id=?
    '''
    params = [user_id]

    if crop_filter:
        query += ' AND cr.crop_name=?'
        params.append(crop_filter)
    if search:
        query += ' AND (ca.activity_name LIKE ? OR cr.crop_name LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    query += ' ORDER BY at.scheduled_date ASC'

    rows = conn.execute(query, params).fetchall()
    conn.close()

    today = date.today()
    acts = []
    for row in rows:
        r = dict(row)
        if r['status'] not in ('completed', 'delayed'):
            days = get_days_remaining(r['scheduled_date'])
            if days is None:
                r['live_status'] = 'upcoming'
                r['days_remaining'] = None
            elif days < 0:
                r['live_status'] = 'overdue'
                r['days_remaining'] = days
            elif days == 0:
                r['live_status'] = 'due_today'
                r['days_remaining'] = 0
            else:
                r['live_status'] = 'upcoming'
                r['days_remaining'] = days
        else:
            r['live_status'] = r['status']
            r['days_remaining'] = None
        acts.append(r)

    # Apply live status filter
    if status_filter != 'all':
        acts = [a for a in acts if a['live_status'] == status_filter]

    # Get crop list for filter dropdown
    conn2 = get_db()
    crop_list = conn2.execute('''SELECT DISTINCT cr.crop_name FROM farmer_crops fc
        JOIN crops cr ON fc.crop_id=cr.id WHERE fc.user_id=?''', (user_id,)).fetchall()
    conn2.close()

    return render_template('activities.html', activities=acts,
        status_filter=status_filter, crop_filter=crop_filter,
        search=search, crop_list=crop_list)

@app.route('/mark_activity/<int:act_id>', methods=['POST'])
@login_required
def mark_activity(act_id):
    user_id = session['user_id']
    new_status = request.form.get('status', 'completed')
    conn = get_db()
    # Security: ensure this activity belongs to the logged-in user
    row = conn.execute('''SELECT at.id FROM activity_tracking at
        JOIN farmer_crops fc ON at.farmer_crop_id=fc.id
        WHERE at.id=? AND fc.user_id=?''', (act_id, user_id)).fetchone()
    if row:
        today_str = date.today().strftime('%Y-%m-%d')
        if new_status == 'completed':
            conn.execute(
                "UPDATE activity_tracking SET status='completed', completed_date=? WHERE id=?",
                (today_str, act_id)
            )
        else:
            conn.execute(
                "UPDATE activity_tracking SET status='delayed' WHERE id=?",
                (act_id,)
            )
        conn.commit()
        flash(f'Activity marked as {new_status}.', 'success')
    conn.close()
    return redirect(request.referrer or url_for('activities'))

@app.route('/api/activity_detail/<int:act_id>')
@login_required
def activity_detail(act_id):
    user_id = session['user_id']
    conn = get_db()
    row = conn.execute('''
        SELECT at.id, at.scheduled_date, at.status, at.completed_date, at.notes,
               ca.activity_name, ca.description,
               cr.crop_name, cr.variety
        FROM activity_tracking at
        JOIN farmer_crops fc ON at.farmer_crop_id=fc.id
        JOIN crop_activities ca ON at.activity_id=ca.id
        JOIN crops cr ON fc.crop_id=cr.id
        WHERE at.id=? AND fc.user_id=?
    ''', (act_id, user_id)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    d = dict(row)
    days = get_days_remaining(d['scheduled_date'])
    if d['status'] not in ('completed', 'delayed'):
        if days is None:
            d['live_status'] = 'upcoming'
        elif days < 0:
            d['live_status'] = 'overdue'
        elif days == 0:
            d['live_status'] = 'due_today'
        else:
            d['live_status'] = 'upcoming'
    else:
        d['live_status'] = d['status']
    d['days_remaining'] = days
    return jsonify(d)


# ─────────────────────────────────────────────
# ROUTES – REPORTS
# ─────────────────────────────────────────────

@app.route('/reports')
@login_required
def reports():
    user_id = session['user_id']
    conn = get_db()
    today = date.today()

    # Overall stats
    total_crops = conn.execute(
        'SELECT COUNT(*) FROM farmer_crops WHERE user_id=?', (user_id,)
    ).fetchone()[0]

    # Per-crop progress
    crops_data = conn.execute('''
        SELECT fc.id, cr.crop_name, cr.variety, cr.season, fc.sowing_date,
               fc.expected_harvest_date, fc.status
        FROM farmer_crops fc JOIN crops cr ON fc.crop_id=cr.id
        WHERE fc.user_id=? ORDER BY fc.created_at DESC
    ''', (user_id,)).fetchall()

    report_rows = []
    for fc in crops_data:
        total = conn.execute(
            'SELECT COUNT(*) FROM activity_tracking WHERE farmer_crop_id=?', (fc['id'],)
        ).fetchone()[0]
        done = conn.execute(
            "SELECT COUNT(*) FROM activity_tracking WHERE farmer_crop_id=? AND status='completed'", (fc['id'],)
        ).fetchone()[0]
        delayed = conn.execute(
            "SELECT COUNT(*) FROM activity_tracking WHERE farmer_crop_id=? AND status='delayed'", (fc['id'],)
        ).fetchone()[0]
        pct = round((done / total * 100) if total > 0 else 0, 1)

        # Live overdue count
        pending = conn.execute(
            '''SELECT scheduled_date FROM activity_tracking WHERE farmer_crop_id=?
               AND status NOT IN ('completed','delayed')''', (fc['id'],)
        ).fetchall()
        overdue_count = sum(1 for p in pending if get_days_remaining(p['scheduled_date']) is not None and get_days_remaining(p['scheduled_date']) < 0)

        report_rows.append({
            **dict(fc),
            'total': total,
            'completed': done,
            'delayed': delayed,
            'overdue': overdue_count,
            'pending': total - done - delayed,
            'progress': pct
        })

    conn.close()
    return render_template('reports.html', total_crops=total_crops,
        report_rows=report_rows, today=today)


# ─────────────────────────────────────────────
# ROUTES – CROP RECOMMENDATION
# ─────────────────────────────────────────────

@app.route('/recommendation')
@login_required
def recommendation():
    return render_template('recommendation.html')


# ─────────────────────────────────────────────
# ROUTES – PROFILE
# ─────────────────────────────────────────────

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        new_pass = request.form.get('new_password', '').strip()

        if not name or not location:
            flash('Name and location are required.', 'danger')
        else:
            if new_pass:
                conn.execute(
                    'UPDATE users SET name=?, location=?, password_hash=? WHERE id=?',
                    (name, location, hash_password(new_pass), user_id)
                )
            else:
                conn.execute('UPDATE users SET name=?, location=? WHERE id=?', (name, location, user_id))
            conn.commit()
            session['user_name'] = name
            flash('Profile updated successfully.', 'success')
            user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()

    conn.close()
    return render_template('profile.html', user=user)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
