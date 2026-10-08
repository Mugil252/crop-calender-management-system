# 🌾 Smart Crop Calendar Management System
### *Real-Time Agricultural Activity Tracking*
> **AI & Data Science Undergraduate Mini Project**

---

## 📌 Project Overview
A web-based system that helps farmers manage crop activities from sowing to harvesting. The farmer selects a crop, enters the sowing date, and the system **automatically calculates all activity dates** based on crop-specific schedules.

---

## 🛠 Technology Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Frontend   | HTML5, CSS3, JavaScript, Bootstrap 5 |
| Backend    | Python Flask                      |
| Database   | SQLite (built-in)                 |
| Charts     | Chart.js 4                        |
| Calendar   | FullCalendar.js 6                 |

---

## 📁 Project Structure

```
crop_calendar/
├── app.py                  ← Flask application (main)
├── database.db             ← SQLite database (auto-created)
├── requirements.txt        ← Python dependencies
│
├── templates/
│   ├── base.html           ← Base layout with sidebar
│   ├── login.html          ← Login page
│   ├── register.html       ← Registration page
│   ├── dashboard.html      ← Main dashboard
│   ├── crops.html          ← My Crops list
│   ├── add_crop.html       ← Add new crop form
│   ├── calendar.html       ← Interactive calendar
│   ├── activities.html     ← Activity tracking table
│   ├── reports.html        ← Reports & charts
│   ├── recommendation.html ← AI crop recommendation
│   └── profile.html        ← User profile
│
└── static/
    ├── css/style.css       ← Custom CSS (green agri theme)
    └── js/script.js        ← Frontend JavaScript
```

---

## ⚙️ Installation & Setup

### Step 1 – Install Python
Download Python 3.10+ from https://python.org and install it.
Make sure to check **"Add Python to PATH"** during installation.

### Step 2 – Create a Virtual Environment (recommended)
Open Command Prompt / Terminal in the `crop_calendar/` folder:

```bash
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Mac/Linux:
source venv/bin/activate
```

### Step 3 – Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 – Run the Application

```bash
python app.py
```

### Step 5 – Open in Browser
Visit: **http://localhost:5000**

---

## 🔑 Demo Login Credentials

| Field    | Value          |
|----------|----------------|
| Mobile   | `9876543210`   |
| Password | `farmer123`    |

---

## 🌱 Supported Crops (10 Crops)

| # | Crop        | Duration | Best Season |
|---|-------------|----------|-------------|
| 1 | Rice/Paddy  | 120–130d | Kharif/Rabi |
| 2 | Maize       | 90–100d  | Kharif/Rabi |
| 3 | Groundnut   | 110–120d | Kharif      |
| 4 | Cotton      | 180–190d | Kharif      |
| 5 | Chilli      | 150–160d | Kharif/Rabi |
| 6 | Tomato      | 110–120d | Rabi        |
| 7 | Brinjal     | 130–140d | All Season  |
| 8 | Onion       | 110–120d | Rabi        |
| 9 | Ragi        | 100–110d | Kharif      |
|10 | Sugarcane   | 360–365d | Annual      |

---

## 📊 Key Features

- ✅ Farmer Registration & Login (with SHA-256 password hashing)
- ✅ Dashboard with live stats, reminders, and charts
- ✅ Add crops → auto-generate activity calendar
- ✅ Interactive FullCalendar with color-coded activities
- ✅ Activity tracking (Complete / Delay)
- ✅ Real-time status (Upcoming / Due Today / Overdue / Delayed)
- ✅ Search & filter activities
- ✅ Detailed reports with Chart.js visualizations
- ✅ AI rule-based crop recommendation
- ✅ Crop progress percentage with progress bars
- ✅ Responsive mobile-friendly design

---

## 🗄 Database Schema

```
users           → id, name, mobile, location, password_hash
crops           → id, crop_name, variety, season, duration_days, soil_type, water_requirement
crop_activities → id, crop_id, activity_name, day_after_sowing, description
farmer_crops    → id, user_id, crop_id, sowing_date, expected_harvest_date, status
activity_tracking → id, farmer_crop_id, activity_id, scheduled_date, status, completed_date
```

---

## 🤖 AI Module
The **Smart Crop Recommendation** uses a rule-based expert system:
- **Input:** Soil type + Season + Water availability
- **Output:** Recommended crop + Reason + Key activities
- Easily extendable to ML (Decision Tree / Naive Bayes)

---

## 📝 Sample Activities Generated (Rice/Paddy – 120 days)

| Day | Activity               |
|-----|------------------------|
| 0   | Land Preparation       |
| 0   | Nursery Preparation    |
| 21  | Transplanting          |
| 25  | First Weeding          |
| 35  | Tillering Fertilizer   |
| 40  | Pest Monitoring        |
| 55  | Panicle Fertilizer     |
| 110 | Harvesting             |

---

## 🎓 Academic Note
This project demonstrates:
- **AI/ML Concept:** Rule-based inference system
- **Data Science:** Progress analytics, status computation
- **Software Engineering:** MVC pattern using Flask
- **Database:** Relational schema with SQLite

---

*Developed as part of AI & Data Science B.Tech Mini Project*
