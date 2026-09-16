# 🏠 RentPG - Modern Room & PG Rental Management System

A full-featured web application designed for students and working professionals to find, inspect, and book verified Paying Guest (PG) and room accommodations with zero brokerage, while enabling PG landlords to manage room vacancies, collect rent, and address tenant maintenance requests online.

---

## 🌟 Key Features

### 🔍 For Tenants & Room Seekers:
- **Smart Search & Filters**: Filter accommodations by City (Bangalore, Pune, Hyderabad, Delhi NCR, Chennai), Gender category (**Boys PG**, **Girls PG**, **Co-ed Coliving**), Room sharing type (Single private room, 2-sharing, 3-sharing, 4-sharing), Budget slider, and Amenities.
- **Detailed Property Showcase**: High-resolution photos, food inclusion details & meal timings, house rules, and room vacancy breakdown.
- **Schedule Free Physical Visits**: Select date and time slot to inspect the property in person.
- **Instant Bed Reservation**: Book a bed online with instant confirmation and bed availability updates.
- **Online Rent Invoicing**: Track monthly rent dues, simulate online payments (UPI, Cards, Net Banking), and download/print official **HRA-compliant Rent Receipts**.
- **Maintenance Ticketing Desk**: Raise service complaints (Plumbing, Electrical, Wi-Fi, Cleaning, AC, Food) and track real-time resolution notes from the landlord.

### 🏢 For PG Landlords & Property Owners:
- **Operations Console**: Real-time metrics on total beds, occupancy rate, vacant beds, collected rent, and outstanding dues.
- **Property & Room Inventory Manager**: Add new PGs, create rooms, and adjust vacant bed counts with a single click.
- **Booking & Visit Management**: Accept or reject incoming bed reservations and view scheduled tenant visits.
- **Rent Collection Ledger**: Track tenant payments and record direct cash/UPI transactions.
- **Tenant Complaints Resolution**: View maintenance tickets logged by tenants and update their status (`In Progress`, `Resolved`) with response notes.

### 🛡️ For System Administrators:
- **Moderation & Control Center**: System-wide statistics, user directory, and ability to verify or disable listings.

---

## 🛠️ Technology Stack

- **Backend**: Python 3 (Flask, Jinja2, Werkzeug Security)
- **Database**: SQLite3 (embedded, zero-configuration)
- **Frontend**: HTML5, Modern Responsive Tailwind CSS (via CDN), FontAwesome 6
- **Testing**: Python `unittest` integration test suite

---

## 🚀 Quick Start Guide

### 1. Requirements
Ensure Python 3.8+ is installed on your system.

```bash
python --version
```

### 2. Install Dependencies (Optional / Pre-installed)
Dependencies are already part of standard Python + Flask:
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Sample Data
Populate the database with realistic sample PGs across Bangalore, Pune, Hyderabad, Delhi, and Chennai:
```bash
python seed.py
```

### 4. Run the Web Application
```bash
python app.py
```

Open your browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Pre-Configured Demo Accounts

On the [Login Page](http://127.0.0.1:5000/login), you can either click the **1-Click Demo Buttons** or log in manually with:

| Role | Email | Password | What You Can Test |
| :--- | :--- | :--- | :--- |
| **Tenant** | `rahul@example.com` | `password123` | View active stay, pay monthly rent, print receipt, submit maintenance complaints |
| **PG Owner** | `rajesh.owner@example.com` | `password123` | Manage Bangalore PGs, adjust vacant beds, approve bookings, resolve complaints |
| **Admin** | `admin@rentpg.com` | `password123` | Platform analytics, user accounts, moderate listings |

---

## 🧪 Running Automated Tests

A comprehensive integration test suite is included to verify all user flows, booking actions, bed decrements, rent payments, and complaints:

```bash
python test_app.py
```

Expected result:
```
Ran 6 tests in ~1.7s
OK
```

---

## 📁 Codebase Directory Structure

```
room-pg-rental/
│
├── app.py                     # Main Flask web application, routing, and controllers
├── database.py                # Database connection, tables schema & initialization
├── seed.py                    # Seed script with realistic PGs, rooms, users, and bookings
├── test_app.py                # Automated integration tests
├── requirements.txt           # Python package requirements
├── README.md                  # Project documentation
│
├── static/
│   ├── css/
│   │   └── style.css          # Badges, glassmorphism, fonts & print styles
│   └── js/
│       └── main.js            # Client-side modal dismissal and interactions
│
└── templates/
    ├── base.html              # Base layout with navbar, alerts & footer
    ├── index.html             # Homepage: Hero search, featured PGs, how it works
    ├── listings.html          # Browse & search filter page
    ├── listing_detail.html    # Detailed PG view with room inventory & booking modals
    ├── login.html             # Sign in with 1-click demo buttons
    ├── register.html          # User registration (Tenant vs PG Owner)
    ├── tenant_dashboard.html  # Tenant portal: Active stays, rent payments & tickets
    ├── owner_dashboard.html   # Owner portal: Vacancies, bookings, visits & complaints
    ├── admin_dashboard.html   # Super admin moderation panel
    ├── add_property.html      # Owner form to register a new PG accommodation
    └── receipt.html           # Official printable/downloadable rent invoice receipt
```
