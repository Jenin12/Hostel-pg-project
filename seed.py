import sqlite3
import json
from werkzeug.security import generate_password_hash
from database import init_db, get_db_connection

def seed_database():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing data if any
    cursor.execute("DELETE FROM complaints;")
    cursor.execute("DELETE FROM payments;")
    cursor.execute("DELETE FROM visits;")
    cursor.execute("DELETE FROM bookings;")
    cursor.execute("DELETE FROM amenities;")
    cursor.execute("DELETE FROM rooms;")
    cursor.execute("DELETE FROM properties;")
    cursor.execute("DELETE FROM users;")
    try:
        cursor.execute("DELETE FROM sqlite_sequence;")
    except sqlite3.OperationalError:
        pass

    # 1. Create Users
    default_password = generate_password_hash("password123")
    
    users = [
        ("Rahul Sharma", "rahul@example.com", "+91 98765 43210", default_password, "tenant"),
        ("Priya Nair", "priya@example.com", "+91 98765 43211", default_password, "tenant"),
        ("Amit Verma", "amit@example.com", "+91 98765 43212", default_password, "tenant"),
        ("Rajesh Kumar (Owner)", "rajesh.owner@example.com", "+91 98123 45678", default_password, "owner"),
        ("Anita Desai (Owner)", "anita.owner@example.com", "+91 98234 56789", default_password, "owner"),
        ("Admin RentPG", "admin@rentpg.com", "+91 99999 00000", default_password, "admin"),
    ]

    cursor.executemany("""
    INSERT INTO users (name, email, phone, password_hash, role)
    VALUES (?, ?, ?, ?, ?)
    """, users)

    owner1_id = cursor.execute("SELECT id FROM users WHERE email='rajesh.owner@example.com'").fetchone()["id"]
    owner2_id = cursor.execute("SELECT id FROM users WHERE email='anita.owner@example.com'").fetchone()["id"]
    tenant1_id = cursor.execute("SELECT id FROM users WHERE email='rahul@example.com'").fetchone()["id"]
    tenant2_id = cursor.execute("SELECT id FROM users WHERE email='priya@example.com'").fetchone()["id"]

    # 2. Properties List
    properties_data = [
        {
            "owner_id": owner1_id,
            "title": "Stanza Living Serene - Luxury Co-ed PG",
            "description": "Modern fully furnished co-living space with high-speed WiFi, hygienic food, gaming lounge, and gym. Located 5 minutes from Manyata Tech Park.",
            "address": "4th Cross, Nagavara Outer Ring Road, Near Manyata Tech Park",
            "locality": "Nagavara",
            "city": "Bangalore",
            "gender_category": "Co-ed",
            "food_included": 1,
            "food_details": "4 Meals Daily (Breakfast, Lunch, Evening Snack, Dinner). North & South Indian Menu, Weekend Special Biryani & Desserts.",
            "rules": "Gate closes at 11:00 PM. Alcohol and smoking strictly prohibited inside premises. Visitors allowed in lounge till 8:00 PM.",
            "images": json.dumps([
                "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&w=1200&q=80",
            ]),
            "contact_phone": "+91 98123 45678",
            "rooms": [
                ("101", "Single", 1, 1, 15000, 30000),
                ("102", "2-Sharing", 2, 1, 9500, 19000),
                ("103", "3-Sharing", 3, 2, 7500, 15000),
            ],
            "amenities": ["High-Speed WiFi", "Air Conditioner", "3 Times Food", "Attached Bathroom", "Daily Housekeeping", "Washing Machine", "Power Backup", "Gym", "CCTV Security"]
        },
        {
            "owner_id": owner1_id,
            "title": "Sri Sai Balaji Luxury PG for Gents",
            "description": "Affordable and premium stay for students and IT professionals. Close to Metro station, bus stops, and major IT companies in Koramangala.",
            "address": "80 Feet Road, 4th Block, Koramangala",
            "locality": "Koramangala",
            "city": "Bangalore",
            "gender_category": "Boys",
            "food_included": 1,
            "food_details": "Homestyle South & North Indian hygienic food. Unlimited breakfast and dinner on weekdays, lunch on weekends.",
            "rules": "No outside guests allowed in rooms after 9:30 PM. Maintain silence during study/sleep hours.",
            "images": json.dumps([
                "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1540518614846-7ede433c4ef7?auto=format&fit=crop&w=1200&q=80",
            ]),
            "contact_phone": "+91 98123 45678",
            "rooms": [
                ("201", "Single", 1, 0, 13000, 26000),
                ("202", "2-Sharing", 2, 2, 8500, 17000),
                ("203", "3-Sharing", 3, 1, 6500, 13000),
                ("204", "4-Sharing", 4, 3, 5500, 11000),
            ],
            "amenities": ["High-Speed WiFi", "3 Times Food", "Attached Bathroom", "Washing Machine", "Power Backup", "CCTV Security", "RO Drinking Water"]
        },
        {
            "owner_id": owner2_id,
            "title": "GreenView Comfort PG for Ladies",
            "description": "Safe, secure, and serene accommodation exclusively for working women and female college students with 24/7 security guard, CCTV, and biometric entry.",
            "address": "Lane 7, Near South Main Road, Koregaon Park",
            "locality": "Koregaon Park",
            "city": "Pune",
            "gender_category": "Girls",
            "food_included": 1,
            "food_details": "Nutritious home-cooked food. Special diet / fruits available on request. Morning tea/coffee provided.",
            "rules": "Biometric curfew at 10:00 PM. Female visitors allowed in lobby area. ID verification mandatory for all check-ins.",
            "images": json.dumps([
                "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=1200&q=80",
            ]),
            "contact_phone": "+91 98234 56789",
            "rooms": [
                ("A-1", "Single", 1, 1, 14000, 28000),
                ("A-2", "2-Sharing", 2, 2, 9000, 18000),
                ("A-3", "3-Sharing", 3, 1, 7000, 14000),
            ],
            "amenities": ["High-Speed WiFi", "Air Conditioner", "3 Times Food", "Attached Bathroom", "Daily Housekeeping", "Washing Machine", "Biometric Access", "24/7 Security Guard", "Power Backup"]
        },
        {
            "owner_id": owner2_id,
            "title": "CyberNest Executive Co-living & PG",
            "description": "Premium co-living space designed for tech workers in Hitec City. Workstations in every room, high-speed fiber internet, and rooftop recreation zone.",
            "address": "Plot 42, Silicon Valley, Madhapur, Hitec City",
            "locality": "Madhapur",
            "city": "Hyderabad",
            "gender_category": "Co-ed",
            "food_included": 1,
            "food_details": "Multi-cuisine buffet breakfast and dinner. Self-cooking induction kitchen available on each floor.",
            "rules": "Flexible night entry with RFID keycard. Decibel restrictions after 11 PM. Cleanliness in shared kitchen is mandatory.",
            "images": json.dumps([
                "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            ]),
            "contact_phone": "+91 98234 56789",
            "rooms": [
                ("301", "Single", 1, 1, 16500, 33000),
                ("302", "2-Sharing", 2, 2, 10500, 21000),
            ],
            "amenities": ["High-Speed WiFi", "Air Conditioner", "3 Times Food", "Attached Bathroom", "Dedicated Workstation", "Power Backup", "Gym", "Rooftop Terrace", "CCTV Security"]
        },
        {
            "owner_id": owner1_id,
            "title": "Elite Scholars Boys Hostel & PG",
            "description": "Quiet, study-friendly environment for university students and aspirants. Spacious desk in every room and 100 Mbps leased line.",
            "address": "Near North Campus, Vijay Nagar",
            "locality": "North Campus",
            "city": "Delhi NCR",
            "gender_category": "Boys",
            "food_included": 1,
            "food_details": "4 Times Homestyle Meals (Breakfast, Lunch, Evening snacks with Tea, Dinner). Milk available at night.",
            "rules": "Strict study hours from 8:00 PM to 11:00 PM. No loud music. Cleanliness inspection every Sunday.",
            "images": json.dumps([
                "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
            ]),
            "contact_phone": "+91 98123 45678",
            "rooms": [
                ("101", "Single", 1, 1, 12000, 24000),
                ("102", "2-Sharing", 2, 1, 8000, 16000),
                ("103", "3-Sharing", 3, 2, 6000, 12000),
            ],
            "amenities": ["High-Speed WiFi", "Air Conditioner", "3 Times Food", "Attached Bathroom", "Study Table", "RO Drinking Water", "Daily Housekeeping"]
        },
        {
            "owner_id": owner2_id,
            "title": "ComfortStay Ladies Living Space",
            "description": "Chic and modern female PG with designer furnishings, attached balcony in select rooms, and direct bus connectivity to Tidel Park.",
            "address": "Thiruvanmiyur Beach Road, Near ECR Junction",
            "locality": "Thiruvanmiyur",
            "city": "Chennai",
            "gender_category": "Girls",
            "food_included": 1,
            "food_details": "Fresh authentic South Indian and North Indian food prepared by experienced cooks. Filter coffee served daily.",
            "rules": "Entry allowed up to 10:30 PM. Non-resident male guests not allowed inside residential floors.",
            "images": json.dumps([
                "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=1200&q=80",
            ]),
            "contact_phone": "+91 98234 56789",
            "rooms": [
                ("B-101", "Single", 1, 1, 13500, 27000),
                ("B-102", "2-Sharing", 2, 2, 8500, 17000),
                ("B-103", "3-Sharing", 3, 3, 6500, 13000),
            ],
            "amenities": ["High-Speed WiFi", "Air Conditioner", "3 Times Food", "Attached Balcony", "Attached Bathroom", "Washing Machine", "Power Backup", "CCTV Security"]
        }
    ]

    for p in properties_data:
        cursor.execute("""
        INSERT INTO properties (owner_id, title, description, address, locality, city, gender_category, food_included, food_details, rules, images, contact_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["owner_id"], p["title"], p["description"], p["address"], p["locality"], p["city"],
            p["gender_category"], p["food_included"], p["food_details"], p["rules"], p["images"], p["contact_phone"]
        ))
        property_id = cursor.lastrowid

        for r in p["rooms"]:
            cursor.execute("""
            INSERT INTO rooms (property_id, room_number, room_type, total_beds, available_beds, monthly_rent, security_deposit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (property_id, r[0], r[1], r[2], r[3], r[4], r[5]))

        for a in p["amenities"]:
            cursor.execute("""
            INSERT INTO amenities (property_id, name, icon)
            VALUES (?, ?, ?)
            """, (property_id, a, "check-circle"))

    # 3. Create active demo booking for tenant1 (Rahul Sharma)
    first_prop = cursor.execute("SELECT id FROM properties LIMIT 1").fetchone()["id"]
    first_room = cursor.execute("SELECT id, monthly_rent FROM rooms WHERE property_id=? LIMIT 1", (first_prop,)).fetchone()
    
    cursor.execute("""
    INSERT INTO bookings (tenant_id, room_id, property_id, check_in_date, rent_amount, status, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tenant1_id, first_room["id"], first_prop, "2026-08-01", first_room["monthly_rent"], "Active", "Student booking with College ID"))
    booking_id = cursor.lastrowid

    # 4. Create Rent Payments for Rahul
    cursor.execute("""
    INSERT INTO payments (booking_id, tenant_id, property_id, month_year, amount, payment_method, transaction_ref, status, paid_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (booking_id, tenant1_id, first_prop, "August 2026", first_room["monthly_rent"], "UPI", "UPI982348123491", "Paid", "2026-08-05 10:30:00"))

    cursor.execute("""
    INSERT INTO payments (booking_id, tenant_id, property_id, month_year, amount, payment_method, transaction_ref, status, paid_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (booking_id, tenant1_id, first_prop, "September 2026", first_room["monthly_rent"], "UPI", "UPI982348991204", "Paid", "2026-09-04 14:15:00"))

    # 5. Create a Scheduled Visit for tenant2 (Priya)
    prop_pune = cursor.execute("SELECT id FROM properties WHERE city='Pune' LIMIT 1").fetchone()["id"]
    cursor.execute("""
    INSERT INTO visits (tenant_id, property_id, visit_date, visit_time, notes, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (tenant2_id, prop_pune, "2026-09-20", "11:30 AM", "Interested in 2-sharing room with balcony", "Scheduled"))

    # 6. Create Maintenance Complaints
    cursor.execute("""
    INSERT INTO complaints (tenant_id, property_id, room_number, title, category, description, status, resolution_notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tenant1_id, first_prop, "101", "Bathroom tap leaking", "Plumbing", 
        "The hot water tap in attached bathroom 101 has a slow continuous drip.", 
        "In Progress", "Plumber notified, scheduled to visit today at 4 PM"
    ))

    cursor.execute("""
    INSERT INTO complaints (tenant_id, property_id, room_number, title, category, description, status, resolution_notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tenant1_id, first_prop, "101", "Wi-Fi speed fluctuation", "WiFi / Internet", 
        "WiFi disconnects occasionally on the 1st floor router during peak evenings.", 
        "Resolved", "Rebooted main fiber ONT and changed channel to 5GHz"
    ))

    conn.commit()
    conn.close()
    print("Database successfully seeded with realistic PGs, rooms, users, bookings, payments, and tickets!")

if __name__ == "__main__":
    seed_database()
