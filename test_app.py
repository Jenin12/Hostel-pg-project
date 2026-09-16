import unittest
import json
from app import app
from database import init_db, get_db_connection
from seed import seed_database

class RoomPGRentalTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        seed_database()

    def test_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"RentPG", response.data)
        self.assertIn(b"Stanza Living Serene", response.data)

    def test_listings_and_filters(self):
        # All listings
        response = self.client.get("/listings")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Explore Rooms", response.data)

        # Filter by city = Pune
        response = self.client.get("/listings?city=Pune")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"GreenView Comfort PG", response.data)
        self.assertNotIn(b"Stanza Living Serene", response.data)

        # Filter by gender = Boys
        response = self.client.get("/listings?gender=Boys")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sri Sai Balaji", response.data)

    def test_listing_detail(self):
        conn = get_db_connection()
        prop = conn.execute("SELECT id FROM properties LIMIT 1").fetchone()
        conn.close()

        response = self.client.get(f"/listing/{prop['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Room Types & Vacancy Status", response.data)
        self.assertIn(b"Schedule Free Physical Visit", response.data)

    def test_quick_logins(self):
        # Tenant
        res_tenant = self.client.get("/quick-login/tenant", follow_redirects=True)
        self.assertEqual(res_tenant.status_code, 200)
        self.assertIn(b"Tenant Portal", res_tenant.data)

        # Owner
        res_owner = self.client.get("/quick-login/owner", follow_redirects=True)
        self.assertEqual(res_owner.status_code, 200)
        self.assertIn(b"Owner Operations Console", res_owner.data)

        # Admin
        res_admin = self.client.get("/quick-login/admin", follow_redirects=True)
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b"Platform Control Center", res_admin.data)

    def test_book_room_and_rent_flow(self):
        # Log in as tenant
        self.client.get("/quick-login/tenant", follow_redirects=True)

        # Get room with availability
        conn = get_db_connection()
        room = conn.execute("SELECT * FROM rooms WHERE available_beds > 0 LIMIT 1").fetchone()
        prop_id = room["property_id"]
        initial_beds = room["available_beds"]
        conn.close()

        # Book room
        res = self.client.post(f"/book-room/{prop_id}", data={
            "room_id": room["id"],
            "check_in_date": "2026-10-01",
            "notes": "College student booking test"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Room booked successfully", res.data)

        # Check beds decreased
        conn = get_db_connection()
        updated_room = conn.execute("SELECT available_beds FROM rooms WHERE id = ?", (room["id"],)).fetchone()
        self.assertEqual(updated_room["available_beds"], initial_beds - 1)

        # Check pending payment created
        tenant = conn.execute("SELECT id FROM users WHERE email = 'rahul@example.com'").fetchone()
        pending_payment = conn.execute("SELECT * FROM payments WHERE tenant_id = ? AND status = 'Pending' ORDER BY id DESC LIMIT 1", (tenant["id"],)).fetchone()
        self.assertIsNotNone(pending_payment)
        payment_id = pending_payment["id"]
        conn.close()

        # Pay rent
        res_pay = self.client.post(f"/tenant/pay-rent/{payment_id}", data={
            "payment_method": "UPI"
        }, follow_redirects=True)
        self.assertEqual(res_pay.status_code, 200)
        self.assertIn(b"Payment successful", res_pay.data)

        # Verify receipt
        res_rec = self.client.get(f"/receipt/{payment_id}")
        self.assertEqual(res_rec.status_code, 200)
        self.assertIn(b"Official Rent Payment Receipt", res_rec.data)

    def test_complaint_lifecycle(self):
        # Tenant submits complaint
        self.client.get("/quick-login/tenant", follow_redirects=True)
        conn = get_db_connection()
        prop = conn.execute("SELECT id FROM properties LIMIT 1").fetchone()
        conn.close()

        res = self.client.post("/tenant/raise-complaint", data={
            "property_id": prop["id"],
            "room_number": "101",
            "title": "Air Conditioner cooling slow",
            "category": "Air Conditioner",
            "description": "AC takes too long to cool the room."
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Maintenance complaint registered", res.data)

        conn = get_db_connection()
        complaint = conn.execute("SELECT * FROM complaints WHERE title = 'Air Conditioner cooling slow'").fetchone()
        self.assertIsNotNone(complaint)
        complaint_id = complaint["id"]
        conn.close()

        # Owner updates complaint
        self.client.get("/quick-login/owner", follow_redirects=True)
        res_update = self.client.post(f"/owner/complaint/{complaint_id}/update", data={
            "status": "Resolved",
            "resolution_notes": "Cleaned AC air filter and refilled refrigerant gas."
        }, follow_redirects=True)
        self.assertEqual(res_update.status_code, 200)

        conn = get_db_connection()
        updated_c = conn.execute("SELECT status, resolution_notes FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
        self.assertEqual(updated_c["status"], "Resolved")
        self.assertEqual(updated_c["resolution_notes"], "Cleaned AC air filter and refilled refrigerant gas.")
        conn.close()

if __name__ == "__main__":
    unittest.main()
