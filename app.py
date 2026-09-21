import os
import json
import functools
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "room-pg-rental-secret-key-2026-super-secure")

# Ensure database tables exist on startup
init_db()

@app.route("/single")
@app.route("/index.html")
def serve_single():
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"))

# ----------------- Jinja Filters & Context Processors -----------------

@app.template_filter("from_json")
def from_json_filter(val):
    if not val:
        return []
    try:
        return json.loads(val)
    except Exception:
        return [val]

@app.context_processor
def inject_user():
    return dict(
        current_user={
            "id": session.get("user_id"),
            "name": session.get("user_name"),
            "email": session.get("user_email"),
            "role": session.get("role")
        } if session.get("user_id") else None,
        now_year=datetime.now().year
    )

# ----------------- Auth Decorators -----------------

def login_required(role=None):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login", next=request.url))
            if role and session.get("role") != role and session.get("role") != "admin":
                flash("Access denied. You do not have permission for this section.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ----------------- Authentication Routes -----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['name']}!", "success")

            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)

            if user["role"] == "owner":
                return redirect(url_for("owner_dashboard"))
            elif user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("tenant_dashboard"))
        else:
            flash("Invalid email or password. Try demo accounts below.", "danger")

    return render_template("login.html")

@app.route("/quick-login/<role>")
def quick_login(role):
    """Convenient demo one-click login for evaluating all roles"""
    email_map = {
        "tenant": "rahul@example.com",
        "owner": "rajesh.owner@example.com",
        "admin": "admin@rentpg.com"
    }
    target_email = email_map.get(role)
    if not target_email:
        flash("Invalid role specified.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (target_email,)).fetchone()
    conn.close()

    if user:
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["role"] = user["role"]
        flash(f"Logged in as Demo {user['role'].capitalize()}: {user['name']}", "info")
        if user["role"] == "owner":
            return redirect(url_for("owner_dashboard"))
        elif user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("tenant_dashboard"))
    flash("Demo user not found. Please run seed.py first.", "danger")
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "tenant")

        if role not in ["tenant", "owner"]:
            role = "tenant"

        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template("register.html")

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for("login"))

        pwd_hash = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, phone, pwd_hash, role))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        session["user_id"] = user_id
        session["user_name"] = name
        session["user_email"] = email
        session["role"] = role
        flash(f"Account successfully created! Welcome, {name}!", "success")

        if role == "owner":
            return redirect(url_for("owner_dashboard"))
        return redirect(url_for("tenant_dashboard"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("index"))

# ----------------- Public & Seeker Routes -----------------

@app.route("/")
def index():
    conn = get_db_connection()
    # Featured listings
    featured_pgs = conn.execute("""
        SELECT p.*, u.name as owner_name,
               MIN(r.monthly_rent) as min_rent,
               MAX(r.monthly_rent) as max_rent,
               SUM(r.available_beds) as total_available_beds
        FROM properties p
        JOIN users u ON p.owner_id = u.id
        LEFT JOIN rooms r ON p.id = r.property_id
        WHERE p.is_verified = 1
        GROUP BY p.id
        ORDER BY p.id DESC
        LIMIT 6
    """).fetchall()

    # Cities list with count
    city_counts = conn.execute("""
        SELECT city, COUNT(id) as count
        FROM properties
        GROUP BY city
        ORDER BY count DESC
    """).fetchall()

    # Overall platform stats
    stats = {
        "properties": conn.execute("SELECT COUNT(*) as count FROM properties").fetchone()["count"],
        "beds": conn.execute("SELECT COALESCE(SUM(total_beds), 0) as count FROM rooms").fetchone()["count"],
        "cities": conn.execute("SELECT COUNT(DISTINCT city) as count FROM properties").fetchone()["count"],
        "happy_tenants": conn.execute("SELECT COUNT(*) as count FROM bookings WHERE status IN ('Active', 'Completed')").fetchone()["count"] + 150
    }
    conn.close()

    return render_template("index.html", featured_pgs=featured_pgs, city_counts=city_counts, stats=stats)

@app.route("/listings")
def listings():
    conn = get_db_connection()

    search_query = request.args.get("search", "").strip()
    city_filter = request.args.get("city", "").strip()
    gender_filter = request.args.get("gender", "").strip()
    room_type_filter = request.args.get("room_type", "").strip()
    max_rent = request.args.get("max_rent", "").strip()
    food_only = request.args.get("food", "").strip()
    amenity_filter = request.args.get("amenity", "").strip()
    sort = request.args.get("sort", "recommended")

    # Base query
    sql = """
        SELECT p.*, u.name as owner_name,
               MIN(r.monthly_rent) as min_rent,
               MAX(r.monthly_rent) as max_rent,
               SUM(r.available_beds) as total_available_beds,
               SUM(r.total_beds) as total_beds
        FROM properties p
        JOIN users u ON p.owner_id = u.id
        LEFT JOIN rooms r ON p.id = r.property_id
        WHERE p.is_verified = 1
    """
    params = []

    if search_query:
        sql += " AND (p.title LIKE ? OR p.locality LIKE ? OR p.city LIKE ? OR p.description LIKE ?)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term, like_term, like_term])

    if city_filter and city_filter.lower() != "all":
        sql += " AND LOWER(p.city) = LOWER(?)"
        params.append(city_filter)

    if gender_filter and gender_filter.lower() != "all":
        sql += " AND p.gender_category = ?"
        params.append(gender_filter)

    if food_only == "1":
        sql += " AND p.food_included = 1"

    if room_type_filter and room_type_filter.lower() != "all":
        sql += " AND p.id IN (SELECT property_id FROM rooms WHERE room_type = ?)"
        params.append(room_type_filter)

    if amenity_filter:
        sql += " AND p.id IN (SELECT property_id FROM amenities WHERE LOWER(name) LIKE LOWER(?))"
        params.append(f"%{amenity_filter}%")

    sql += " GROUP BY p.id"

    if max_rent:
        try:
            sql += " HAVING min_rent <= ?"
            params.append(float(max_rent))
        except ValueError:
            pass

    if sort == "price_asc":
        sql += " ORDER BY min_rent ASC"
    elif sort == "price_desc":
        sql += " ORDER BY min_rent DESC"
    else:
        sql += " ORDER BY p.id DESC"

    pg_list = conn.execute(sql, params).fetchall()

    # Get distinct cities for filter dropdown
    all_cities = [row["city"] for row in conn.execute("SELECT DISTINCT city FROM properties ORDER BY city").fetchall()]
    conn.close()

    return render_template(
        "listings.html",
        pg_list=pg_list,
        all_cities=all_cities,
        filters={
            "search": search_query,
            "city": city_filter,
            "gender": gender_filter,
            "room_type": room_type_filter,
            "max_rent": max_rent,
            "food": food_only,
            "amenity": amenity_filter,
            "sort": sort
        }
    )

@app.route("/listing/<int:property_id>")
def listing_detail(property_id):
    conn = get_db_connection()
    property_row = conn.execute("""
        SELECT p.*, u.name as owner_name, u.email as owner_email, u.phone as owner_phone
        FROM properties p
        JOIN users u ON p.owner_id = u.id
        WHERE p.id = ?
    """, (property_id,)).fetchone()

    if not property_row:
        conn.close()
        abort(404)

    rooms = conn.execute("SELECT * FROM rooms WHERE property_id = ? ORDER BY monthly_rent ASC", (property_id,)).fetchall()
    amenities = conn.execute("SELECT * FROM amenities WHERE property_id = ?", (property_id,)).fetchall()
    
    # Similar nearby properties
    similar = conn.execute("""
        SELECT p.*, MIN(r.monthly_rent) as min_rent
        FROM properties p
        LEFT JOIN rooms r ON p.id = r.property_id
        WHERE p.city = ? AND p.id != ?
        GROUP BY p.id
        LIMIT 3
    """, (property_row["city"], property_id)).fetchall()

    conn.close()

    return render_template(
        "listing_detail.html",
        property=property_row,
        rooms=rooms,
        amenities=amenities,
        similar=similar
    )

# ----------------- Booking & Visit Actions -----------------

@app.route("/schedule-visit/<int:property_id>", methods=["POST"])
@login_required()
def schedule_visit(property_id):
    visit_date = request.form.get("visit_date")
    visit_time = request.form.get("visit_time")
    notes = request.form.get("notes", "")

    if not visit_date or not visit_time:
        flash("Please select both a date and time slot for your visit.", "danger")
        return redirect(url_for("listing_detail", property_id=property_id))

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO visits (tenant_id, property_id, visit_date, visit_time, notes, status)
        VALUES (?, ?, ?, ?, ?, 'Scheduled')
    """, (session["user_id"], property_id, visit_date, visit_time, notes))
    conn.commit()
    conn.close()

    flash("Visit successfully scheduled! The property manager has been notified.", "success")
    return redirect(url_for("tenant_dashboard"))

@app.route("/book-room/<int:property_id>", methods=["POST"])
@login_required()
def book_room(property_id):
    room_id = request.form.get("room_id")
    check_in_date = request.form.get("check_in_date")
    notes = request.form.get("notes", "")

    if not room_id or not check_in_date:
        flash("Please select a room type and check-in date.", "danger")
        return redirect(url_for("listing_detail", property_id=property_id))

    conn = get_db_connection()
    room = conn.execute("SELECT * FROM rooms WHERE id = ? AND property_id = ?", (room_id, property_id)).fetchone()
    if not room or room["available_beds"] <= 0:
        conn.close()
        flash("Sorry, this room is currently fully occupied. Please pick another room.", "warning")
        return redirect(url_for("listing_detail", property_id=property_id))

    cursor = conn.cursor()
    # Create booking
    cursor.execute("""
        INSERT INTO bookings (tenant_id, room_id, property_id, check_in_date, rent_amount, status, notes)
        VALUES (?, ?, ?, ?, ?, 'Active', ?)
    """, (session["user_id"], room_id, property_id, check_in_date, room["monthly_rent"], notes))
    booking_id = cursor.lastrowid

    # Decrement available bed count
    cursor.execute("UPDATE rooms SET available_beds = available_beds - 1 WHERE id = ?", (room_id,))

    # Create initial rent payment record for current month (Pending)
    current_month = datetime.now().strftime("%B %Y")
    cursor.execute("""
        INSERT INTO payments (booking_id, tenant_id, property_id, month_year, amount, payment_method, status)
        VALUES (?, ?, ?, ?, ?, 'Pending', 'Pending')
    """, (booking_id, session["user_id"], property_id, current_month, room["monthly_rent"]))

    conn.commit()
    conn.close()

    flash("Room booked successfully! Welcome to your new home. View your stay details below.", "success")
    return redirect(url_for("tenant_dashboard"))

# ----------------- Tenant Portal Routes -----------------

@app.route("/tenant/dashboard")
@login_required()
def tenant_dashboard():
    tenant_id = session["user_id"]
    conn = get_db_connection()

    # Active and past bookings
    bookings = conn.execute("""
        SELECT b.*, p.title as property_title, p.address as property_address, p.city as property_city,
               p.contact_phone as property_phone, r.room_number, r.room_type, r.monthly_rent, r.security_deposit
        FROM bookings b
        JOIN properties p ON b.property_id = p.id
        JOIN rooms r ON b.room_id = r.id
        WHERE b.tenant_id = ?
        ORDER BY b.id DESC
    """, (tenant_id,)).fetchall()

    # Payments & Invoices
    payments = conn.execute("""
        SELECT pay.*, p.title as property_title, r.room_number
        FROM payments pay
        JOIN bookings b ON pay.booking_id = b.id
        JOIN properties p ON pay.property_id = p.id
        JOIN rooms r ON b.room_id = r.id
        WHERE pay.tenant_id = ?
        ORDER BY pay.id DESC
    """, (tenant_id,)).fetchall()

    # Scheduled Visits
    visits = conn.execute("""
        SELECT v.*, p.title as property_title, p.address, p.city, p.contact_phone
        FROM visits v
        JOIN properties p ON v.property_id = p.id
        WHERE v.tenant_id = ?
        ORDER BY v.id DESC
    """, (tenant_id,)).fetchall()

    # Complaints submitted
    complaints = conn.execute("""
        SELECT c.*, p.title as property_title
        FROM complaints c
        JOIN properties p ON c.property_id = p.id
        WHERE c.tenant_id = ?
        ORDER BY c.id DESC
    """, (tenant_id,)).fetchall()

    conn.close()

    return render_template(
        "tenant_dashboard.html",
        bookings=bookings,
        payments=payments,
        visits=visits,
        complaints=complaints
    )

@app.route("/tenant/pay-rent/<int:payment_id>", methods=["POST"])
@login_required()
def pay_rent(payment_id):
    payment_method = request.form.get("payment_method", "UPI")
    import random
    tx_ref = f"TXN{datetime.now().strftime('%Y%m%d%H%M')}{random.randint(1000, 9999)}"

    conn = get_db_connection()
    conn.execute("""
        UPDATE payments
        SET status = 'Paid',
            payment_method = ?,
            transaction_ref = ?,
            paid_at = CURRENT_TIMESTAMP
        WHERE id = ? AND tenant_id = ?
    """, (payment_method, tx_ref, payment_id, session["user_id"]))
    conn.commit()
    conn.close()

    flash(f"Payment successful! Rent marked as Paid. Transaction ID: {tx_ref}", "success")
    return redirect(url_for("tenant_dashboard"))

@app.route("/receipt/<int:payment_id>")
@login_required()
def view_receipt(payment_id):
    conn = get_db_connection()
    payment = conn.execute("""
        SELECT pay.*, 
               u.name as tenant_name, u.email as tenant_email, u.phone as tenant_phone,
               p.title as property_title, p.address as property_address, p.city as property_city,
               p.contact_phone as property_phone,
               owner.name as owner_name, owner.phone as owner_phone, owner.email as owner_email,
               r.room_number, r.room_type
        FROM payments pay
        JOIN users u ON pay.tenant_id = u.id
        JOIN properties p ON pay.property_id = p.id
        JOIN users owner ON p.owner_id = owner.id
        JOIN bookings b ON pay.booking_id = b.id
        JOIN rooms r ON b.room_id = r.id
        WHERE pay.id = ?
    """, (payment_id,)).fetchone()
    conn.close()

    if not payment:
        abort(404)

    # Allow access if user is the tenant, owner, or admin
    if session.get("role") != "admin" and session.get("user_id") not in [payment["tenant_id"], payment["owner_id"] if "owner_id" in payment.keys() else None]:
        # check if current user is owner of this property
        conn = get_db_connection()
        is_owner = conn.execute("SELECT id FROM properties WHERE id=? AND owner_id=?", (payment["property_id"], session["user_id"])).fetchone()
        conn.close()
        if not is_owner and session["user_id"] != payment["tenant_id"]:
            flash("Access denied to view this receipt.", "danger")
            return redirect(url_for("index"))

    return render_template("receipt.html", receipt=payment)

@app.route("/tenant/raise-complaint", methods=["POST"])
@login_required()
def raise_complaint():
    property_id = request.form.get("property_id")
    room_number = request.form.get("room_number", "")
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "General")
    description = request.form.get("description", "").strip()

    if not property_id or not title or not description:
        flash("Please provide all required fields to submit your maintenance request.", "danger")
        return redirect(url_for("tenant_dashboard"))

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO complaints (tenant_id, property_id, room_number, title, category, description, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Open')
    """, (session["user_id"], property_id, room_number, title, category, description))
    conn.commit()
    conn.close()

    flash("Maintenance complaint registered! The PG manager has received your ticket.", "success")
    return redirect(url_for("tenant_dashboard"))

# ----------------- Owner Portal Routes -----------------

@app.route("/owner/dashboard")
@login_required(role="owner")
def owner_dashboard():
    owner_id = session["user_id"]
    conn = get_db_connection()

    # My Properties
    properties = conn.execute("""
        SELECT p.*,
               COUNT(DISTINCT r.id) as room_count,
               COALESCE(SUM(r.total_beds), 0) as total_beds,
               COALESCE(SUM(r.available_beds), 0) as available_beds
        FROM properties p
        LEFT JOIN rooms r ON p.id = r.property_id
        WHERE p.owner_id = ?
        GROUP BY p.id
        ORDER BY p.id DESC
    """, (owner_id,)).fetchall()

    # Summary Statistics
    total_props = len(properties)
    total_beds = sum([p["total_beds"] for p in properties])
    vacant_beds = sum([p["available_beds"] for p in properties])
    occupied_beds = total_beds - vacant_beds

    # Bookings for my properties
    bookings = conn.execute("""
        SELECT b.*, u.name as tenant_name, u.phone as tenant_phone, u.email as tenant_email,
               p.title as property_title, r.room_number, r.room_type
        FROM bookings b
        JOIN users u ON b.tenant_id = u.id
        JOIN properties p ON b.property_id = p.id
        JOIN rooms r ON b.room_id = r.id
        WHERE p.owner_id = ?
        ORDER BY b.id DESC
    """, (owner_id,)).fetchall()

    # Scheduled visits for my properties
    visits = conn.execute("""
        SELECT v.*, u.name as tenant_name, u.phone as tenant_phone, u.email as tenant_email,
               p.title as property_title
        FROM visits v
        JOIN users u ON v.tenant_id = u.id
        JOIN properties p ON v.property_id = p.id
        WHERE p.owner_id = ?
        ORDER BY v.id DESC
    """, (owner_id,)).fetchall()

    # Payments received / due
    payments = conn.execute("""
        SELECT pay.*, u.name as tenant_name, p.title as property_title, r.room_number
        FROM payments pay
        JOIN users u ON pay.tenant_id = u.id
        JOIN properties p ON pay.property_id = p.id
        JOIN bookings b ON pay.booking_id = b.id
        JOIN rooms r ON b.room_id = r.id
        WHERE p.owner_id = ?
        ORDER BY pay.id DESC
    """, (owner_id,)).fetchall()

    # Complaints for my properties
    complaints = conn.execute("""
        SELECT c.*, u.name as tenant_name, u.phone as tenant_phone, p.title as property_title
        FROM complaints c
        JOIN users u ON c.tenant_id = u.id
        JOIN properties p ON c.property_id = p.id
        WHERE p.owner_id = ?
        ORDER BY c.id DESC
    """, (owner_id,)).fetchall()

    # Rooms per property
    prop_rooms = {}
    for p in properties:
        rooms = conn.execute("SELECT * FROM rooms WHERE property_id = ?", (p["id"],)).fetchall()
        prop_rooms[p["id"]] = rooms

    total_revenue = sum([pay["amount"] for pay in payments if pay["status"] == "Paid"])
    pending_revenue = sum([pay["amount"] for pay in payments if pay["status"] in ["Pending", "Overdue"]])

    conn.close()

    metrics = {
        "properties": total_props,
        "total_beds": total_beds,
        "occupied_beds": occupied_beds,
        "vacant_beds": vacant_beds,
        "total_revenue": total_revenue,
        "pending_revenue": pending_revenue
    }

    return render_template(
        "owner_dashboard.html",
        properties=properties,
        prop_rooms=prop_rooms,
        bookings=bookings,
        visits=visits,
        payments=payments,
        complaints=complaints,
        metrics=metrics
    )

@app.route("/owner/add-property", methods=["GET", "POST"])
@login_required(role="owner")
def add_property():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        address = request.form.get("address", "").strip()
        locality = request.form.get("locality", "").strip()
        city = request.form.get("city", "").strip()
        gender_category = request.form.get("gender_category", "Co-ed")
        food_included = 1 if request.form.get("food_included") == "1" else 0
        food_details = request.form.get("food_details", "").strip()
        rules = request.form.get("rules", "").strip()
        contact_phone = request.form.get("contact_phone", "").strip()
        image_url = request.form.get("image_url", "").strip()
        amenities_selected = request.form.getlist("amenities")

        if not image_url:
            image_url = "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80"

        images_json = json.dumps([image_url])

        if not title or not address or not city:
            flash("Please enter Property Name, Address, and City.", "danger")
            return render_template("add_property.html")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO properties (owner_id, title, description, address, locality, city, gender_category, food_included, food_details, rules, images, contact_phone, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            session["user_id"], title, description, address, locality, city,
            gender_category, food_included, food_details, rules, images_json, contact_phone
        ))
        property_id = cursor.lastrowid

        # Insert default standard rooms
        default_rooms = [
            ("101", "Single", 1, 1, 12000, 24000),
            ("102", "2-Sharing", 2, 2, 8000, 16000),
            ("103", "3-Sharing", 3, 3, 6000, 12000),
        ]
        for r in default_rooms:
            cursor.execute("""
                INSERT INTO rooms (property_id, room_number, room_type, total_beds, available_beds, monthly_rent, security_deposit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (property_id, r[0], r[1], r[2], r[3], r[4], r[5]))

        # Insert amenities
        for a in amenities_selected:
            cursor.execute("INSERT INTO amenities (property_id, name, icon) VALUES (?, ?, 'check')", (property_id, a))

        conn.commit()
        conn.close()

        flash("New PG successfully registered! You can now manage rooms and vacancies.", "success")
        return redirect(url_for("owner_dashboard"))

    return render_template("add_property.html")

@app.route("/owner/add-room/<int:property_id>", methods=["POST"])
@login_required(role="owner")
def add_room(property_id):
    room_number = request.form.get("room_number", "").strip()
    room_type = request.form.get("room_type", "2-Sharing")
    total_beds = int(request.form.get("total_beds", 2))
    available_beds = int(request.form.get("available_beds", total_beds))
    monthly_rent = float(request.form.get("monthly_rent", 8000))
    security_deposit = float(request.form.get("security_deposit", monthly_rent * 2))

    conn = get_db_connection()
    # verify ownership
    prop = conn.execute("SELECT id FROM properties WHERE id = ? AND owner_id = ?", (property_id, session["user_id"])).fetchone()
    if not prop and session.get("role") != "admin":
        conn.close()
        flash("Unauthorized.", "danger")
        return redirect(url_for("owner_dashboard"))

    conn.execute("""
        INSERT INTO rooms (property_id, room_number, room_type, total_beds, available_beds, monthly_rent, security_deposit)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (property_id, room_number, room_type, total_beds, available_beds, monthly_rent, security_deposit))
    conn.commit()
    conn.close()

    flash(f"Room {room_number} added successfully!", "success")
    return redirect(url_for("owner_dashboard"))

@app.route("/owner/update-beds/<int:room_id>", methods=["POST"])
@login_required(role="owner")
def update_beds(room_id):
    available_beds = int(request.form.get("available_beds", 0))
    conn = get_db_connection()
    conn.execute("UPDATE rooms SET available_beds = ? WHERE id = ?", (available_beds, room_id))
    conn.commit()
    conn.close()
    flash("Vacancy status updated.", "info")
    return redirect(url_for("owner_dashboard"))

@app.route("/owner/booking/<int:booking_id>/<action>", methods=["POST"])
@login_required(role="owner")
def manage_booking(booking_id, action):
    status = "Active" if action == "approve" else "Cancelled"
    conn = get_db_connection()
    conn.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
    conn.commit()
    conn.close()
    flash(f"Booking marked as {status}.", "info")
    return redirect(url_for("owner_dashboard"))

@app.route("/owner/complaint/<int:complaint_id>/update", methods=["POST"])
@login_required(role="owner")
def update_complaint(complaint_id):
    status = request.form.get("status", "In Progress")
    resolution_notes = request.form.get("resolution_notes", "").strip()

    conn = get_db_connection()
    conn.execute("""
        UPDATE complaints
        SET status = ?, resolution_notes = ?
        WHERE id = ?
    """, (status, resolution_notes, complaint_id))
    conn.commit()
    conn.close()

    flash(f"Complaint updated to '{status}'.", "success")
    return redirect(url_for("owner_dashboard"))

@app.route("/owner/mark-rent-paid/<int:payment_id>", methods=["POST"])
@login_required(role="owner")
def mark_rent_paid(payment_id):
    import random
    tx_ref = f"CASH/UPI-{random.randint(10000, 99999)}"
    conn = get_db_connection()
    conn.execute("""
        UPDATE payments
        SET status = 'Paid',
            payment_method = 'Cash / Direct UPI',
            transaction_ref = ?,
            paid_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (tx_ref, payment_id))
    conn.commit()
    conn.close()

    flash("Payment marked as Paid successfully.", "success")
    return redirect(url_for("owner_dashboard"))

# ----------------- Admin Portal Routes -----------------

@app.route("/admin/dashboard")
@login_required(role="admin")
def admin_dashboard():
    conn = get_db_connection()

    stats = {
        "total_users": conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"],
        "total_properties": conn.execute("SELECT COUNT(*) as count FROM properties").fetchone()["count"],
        "total_bookings": conn.execute("SELECT COUNT(*) as count FROM bookings").fetchone()["count"],
        "total_complaints": conn.execute("SELECT COUNT(*) as count FROM complaints").fetchone()["count"],
    }

    properties = conn.execute("""
        SELECT p.*, u.name as owner_name, u.email as owner_email,
               COUNT(r.id) as room_count
        FROM properties p
        JOIN users u ON p.owner_id = u.id
        LEFT JOIN rooms r ON p.id = r.property_id
        GROUP BY p.id
        ORDER BY p.id DESC
    """).fetchall()

    users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("admin_dashboard.html", stats=stats, properties=properties, users=users)

@app.route("/admin/toggle-property/<int:property_id>", methods=["POST"])
@login_required(role="admin")
def toggle_property(property_id):
    conn = get_db_connection()
    current = conn.execute("SELECT is_verified FROM properties WHERE id = ?", (property_id,)).fetchone()
    new_status = 0 if current["is_verified"] == 1 else 1
    conn.execute("UPDATE properties SET is_verified = ? WHERE id = ?", (new_status, property_id))
    conn.commit()
    conn.close()
    flash(f"Property status toggled to {'Verified' if new_status == 1 else 'Disabled'}.", "info")
    return redirect(url_for("admin_dashboard"))

# ----------------- Error Handlers -----------------

@app.errorhandler(404)
def not_found(e):
    return render_template("base.html", error_title="404 - Page Not Found", error_msg="The page or PG accommodation you are looking for does not exist."), 404

if __name__ == "__main__":
    print("Starting Room & PG Rental System on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
