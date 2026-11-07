import hashlib
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.models import TokenRecord


# =========================
# DEAN OFFICE TIMING LOGIC
# =========================

def is_dean_office_open(current_dt: Optional[datetime] = None) -> Tuple[bool, str]:
    """
    Checks if current local time is within Dean office service hours:
    9:00 AM – 1:00 PM and 3:00 PM – 5:00 PM.
    """
    if current_dt is None:
        current_dt = datetime.now()

    cur_time = current_dt.time()
    slot1_start = time(9, 0)
    slot1_end = time(13, 0)
    slot2_start = time(15, 0)
    slot2_end = time(17, 0)

    is_open = (slot1_start <= cur_time <= slot1_end) or (slot2_start <= cur_time <= slot2_end)
    hours_str = "9:00 AM – 1:00 PM & 3:00 PM – 5:00 PM"

    return is_open, hours_str


# =========================
# CROWD STATUS FUNCTION
# =========================

def get_crowd_status(service_id: str, count: int) -> Tuple[str, str]:
    """
    Returns (status_text, status_class) matching frontend crowd logic.
    """
    if service_id == "dean":
        if count <= 5:
            return "Low Crowd", "status-low"
        if count <= 15:
            return "Moderate", "status-medium"
        return "Highly Crowded", "status-high"

    if service_id == "printing":
        if count <= 5:
            return "Low", "status-low"
        if count <= 15:
            return "Busy", "status-medium"
        return "Highly Crowded", "status-high"

    if service_id == "cafe":
        if count <= 3:
            return "Low Crowd", "status-low"
        if count <= 8:
            return "Moderate", "status-medium"
        return "Busy", "status-high"

    return "Normal", "status-low"


# =========================
# PRINTING WAIT TIME ESTIMATION
# =========================

def estimate_printing_time(jobs_ahead: int, copies: int = 1, is_colour: bool = False) -> Tuple[int, str]:
    """
    Estimates how long until the student should reach the printing shop.
    Matches specification:
      P-010 (~5 ahead): ~5 mins
      P-015 (~10 ahead): ~9 mins
      P-020 (~15 ahead): ~13 mins
    """
    # Base calculation: ~0.8 minutes per job ahead + small buffer for copies/color
    base_minutes = max(1, round(1 + (jobs_ahead * 0.8) + (copies * 0.1) + (1 if is_colour else 0)))
    ready_dt = datetime.now() + timedelta(minutes=base_minutes)
    ready_time_str = ready_dt.strftime("%I:%M %p").lstrip("0")

    return base_minutes, f"~{base_minutes} mins ({ready_time_str})"


# =========================
# CAFÉ PREPARATION ESTIMATION
# =========================

def estimate_cafe_prep_time(orders_ahead: int, items: List[Dict]) -> Tuple[int, str]:
    """
    Calculates preparation time based on items selected and orders ahead.
    """
    base_item_prep = 3
    total_quantity = 0

    for item in items:
        qty = item.get("quantity", 1)
        total_quantity += qty

    if total_quantity > 1:
        base_item_prep += min(8, total_quantity * 2)

    total_wait_minutes = base_item_prep + (orders_ahead * 2)

    start_dt = datetime.now() + timedelta(minutes=total_wait_minutes)
    end_dt = start_dt + timedelta(minutes=5)
    start_str = start_dt.strftime("%I:%M").lstrip("0")
    end_str = end_dt.strftime("%I:%M %p").lstrip("0")

    return total_wait_minutes, f"~{total_wait_minutes} mins ({start_str}–{end_str})"


# =========================
# DEAN WAIT TIME ESTIMATION
# =========================

def estimate_dean_wait_time(students_ahead: int, avg_duration_minutes: int = 3) -> Tuple[int, str]:
    """
    Calculates Dean office wait time (~3 minutes per student).
    """
    wait_minutes = max(avg_duration_minutes, students_ahead * avg_duration_minutes)
    ready_dt = datetime.now() + timedelta(minutes=wait_minutes)
    ready_time_str = ready_dt.strftime("%I:%M %p").lstrip("0")

    return wait_minutes, ready_time_str


# =========================
# TOKEN NUMBER GENERATOR
# =========================

def generate_token_number(db: Session, service_id: str, prefix: str) -> Tuple[str, int]:
    """
    Generates clean 3-digit sequential token (e.g., D-001, P-010, C-108).
    """
    last_token = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == service_id)
        .order_by(TokenRecord.sequence.desc())
        .first()
    )

    next_seq = (last_token.sequence + 1) if last_token else 1
    token_str = f"{prefix}-{next_seq:03d}"

    return token_str, next_seq


# =========================
# GENERIC ESTIMATED TIME DISPATCHER
# =========================

def calculate_estimated_time(service_id: str, count: int, avg_duration_minutes: int) -> str:
    """
    Dispatcher that returns a human-readable estimated time string for any service.
    Used by queues.py for the global status endpoint.
    """
    if service_id == "dean":
        _, est_str = estimate_dean_wait_time(count, avg_duration_minutes)
        return est_str
    elif service_id == "printing":
        _, est_str = estimate_printing_time(count)
        return est_str
    elif service_id == "cafe":
        _, est_str = estimate_cafe_prep_time(count, [])
        return est_str
    else:
        from datetime import datetime, timedelta
        ready_dt = datetime.now() + timedelta(minutes=count * avg_duration_minutes)
        return ready_dt.strftime("%I:%M %p").lstrip("0")


# =========================
# PASSWORD HASHING
# =========================

def hash_password(password: str) -> str:
    salt = "inq_campus_salt"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password
