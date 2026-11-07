import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app, init_database
from app.database import Base, engine

client = TestClient(app)

def setup_module(module):
    # Ensure fresh DB initialization
    init_database()

def test_health_and_root():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    res = client.get("/")
    assert res.status_code == 200
    assert "project" in res.json()

def test_queues_status():
    res = client.get("/api/queues/status")
    assert res.status_code == 200
    data = res.json()
    assert "dean" in data
    assert "printing" in data
    assert "cafe" in data
    assert data["dean"]["service"] == "dean"
    assert data["dean"]["service_hours"] == "9:00 AM – 1:00 PM & 3:00 PM – 5:00 PM"

def test_dean_workflow():
    # 1. Check initial Dean status
    status_res = client.get("/api/dean/status")
    assert status_res.status_code == 200
    initial_waiting = status_res.json()["waiting_count"]

    # 2. Student generates Dean token
    token_res = client.post("/api/dean/token", json={"service_option": "Document Verification"})
    assert token_res.status_code == 200
    token_data = token_res.json()
    assert token_data["token_number"].startswith("D-")
    assert token_data["service_id"] == "dean"
    assert token_data["status"] == "waiting"

    # 3. Queue count increments
    status_after = client.get("/api/dean/status").json()
    assert status_after["waiting_count"] == initial_waiting + 1

    # 4. Dean staff starts serving next student
    serve_res = client.post("/api/admin/dean/start-serving")
    assert serve_res.status_code == 200
    serve_data = serve_res.json()
    assert "Now serving token" in serve_data["message"]

    # 5. Dean staff completes work
    comp_res = client.post("/api/admin/dean/complete")
    assert comp_res.status_code == 200
    assert "Completed token" in comp_res.json()["message"]

def test_printing_workflow():
    # 1. Check printing status
    status_res = client.get("/api/printing/status")
    assert status_res.status_code == 200
    initial_waiting = status_res.json()["waiting_jobs_count"]

    # 2. Student submits print job
    token_res = client.post("/api/printing/token", json={
        "file_name": "syllabus.pdf",
        "paper_size": "A4",
        "colour": "Black & White",
        "sides": "Single-sided",
        "pages": "All pages",
        "copies": 2
    })
    assert token_res.status_code == 200
    token_data = token_res.json()
    assert token_data["token_number"].startswith("P-")
    assert token_data["service_id"] == "printing"
    assert "mins" in token_data["estimated_time"]

    # 3. Queue count increases
    status_after = client.get("/api/printing/status").json()
    assert status_after["waiting_jobs_count"] == initial_waiting + 1

def test_cafe_workflow():
    # 1. Fetch menu
    menu_res = client.get("/api/cafe/menu")
    assert menu_res.status_code == 200
    menu = menu_res.json()
    assert len(menu) > 0

    # 2. Place café order
    order_res = client.post("/api/cafe/order", json={
        "items": [
            {"name": "Cold Coffee", "quantity": 1, "price": 25},
            {"name": "Veg Patties", "quantity": 2, "price": 15}
        ],
        "other_item": "Extra straw",
        "notes": "Less ice"
    })
    assert order_res.status_code == 200
    order_data = order_res.json()
    assert order_data["token_number"].startswith("C-")
    assert order_data["service_id"] == "cafe"
    assert "mins" in order_data["estimated_time"]

def test_admin_authentication():
    # Valid login
    login_res = client.post("/api/admin/login", json={
        "username": "dean",
        "password": "dean123"
    })
    assert login_res.status_code == 200
    assert "token" in login_res.json()
    assert login_res.json()["role"] == "dean_staff"

    # Invalid login
    bad_login = client.post("/api/admin/login", json={
        "username": "dean",
        "password": "wrongpassword"
    })
    assert bad_login.status_code == 401

def test_admin_queues_overview():
    res = client.get("/api/admin/queues")
    assert res.status_code == 200
    data = res.json()
    assert "dean" in data
    assert "printing" in data
    assert "cafe" in data

if __name__ == "__main__":
    setup_module(None)
    test_health_and_root()
    print("[PASS] test_health_and_root")
    test_queues_status()
    print("[PASS] test_queues_status")
    test_dean_workflow()
    print("[PASS] test_dean_workflow")
    test_printing_workflow()
    print("[PASS] test_printing_workflow")
    test_cafe_workflow()
    print("[PASS] test_cafe_workflow")
    test_admin_authentication()
    print("[PASS] test_admin_authentication")
    test_admin_queues_overview()
    print("[PASS] test_admin_queues_overview")
    print("\nALL WORKFLOW TESTS PASSED SUCCESSFULLY!")
