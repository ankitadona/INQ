from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import AdminUser, ServiceQueue, TokenRecord
from app.schemas.schemas import AdminActionResponse, LoginRequest, LoginResponse
from app.utils.queue_helpers import (
    estimate_cafe_prep_time,
    estimate_dean_wait_time,
    estimate_printing_time,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/admin", tags=["Admin & Staff Controls"])


def seed_admin_users_if_empty(db: Session):
    default_users = [
        {"username": "dean", "password": "dean123", "role": "dean_staff", "department": "dean"},
        {"username": "printing", "password": "print123", "role": "printing_staff", "department": "printing"},
        {"username": "cafe", "password": "cafe123", "role": "cafe_staff", "department": "cafe"},
        {"username": "admin", "password": "admin123", "role": "super_admin", "department": "all"},
    ]

    if db.query(AdminUser).count() == 0:
        for u in default_users:
            db.add(AdminUser(
                username=u["username"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
                department=u["department"],
            ))
        db.commit()


# =========================
# AUTHENTICATION
# =========================

@router.post("/login", response_model=LoginResponse)
def staff_login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Staff login endpoint.
    Default credentials:
      dean / dean123
      printing / print123
      cafe / cafe123
      admin / admin123
    """
    seed_admin_users_if_empty(db)

    user = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Simple session token
    token = f"inq_token_{user.username}_{user.role}"

    return LoginResponse(
        token=token,
        username=user.username,
        role=user.role,
        department=user.department,
    )


# =========================
# RECALCULATION HELPER
# =========================

def recalculate_service_queue(db: Session, service_id: str):
    """
    Recalculates positions and estimated wait times for all waiting tokens in a service.
    """
    waiting_tokens = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == service_id, TokenRecord.status == "waiting")
        .order_by(TokenRecord.sequence.asc())
        .all()
    )

    service_rec = db.query(ServiceQueue).filter(ServiceQueue.id == service_id).first()
    avg_dur = service_rec.avg_duration_minutes if service_rec else 3

    for idx, token in enumerate(waiting_tokens):
        people_ahead = idx
        if service_id == "dean":
            wait_mins, est_turn = estimate_dean_wait_time(people_ahead + 1, avg_dur)
        elif service_id == "printing":
            wait_mins, est_turn = estimate_printing_time(people_ahead)
        elif service_id == "cafe":
            wait_mins, est_turn = estimate_cafe_prep_time(people_ahead, [])
        else:
            wait_mins, est_turn = (people_ahead * 3, "Soon")

        token.estimated_wait_minutes = wait_mins
        token.estimated_time = est_turn

    db.commit()


# =========================
# LIVE QUEUE OVERVIEW FOR ADMIN
# =========================

@router.get("/queues")
def get_admin_queues_overview(db: Session = Depends(get_db)):
    """
    Returns full queue breakdown for staff dashboard.
    """
    services = ["dean", "printing", "cafe"]
    overview = {}

    for s_id in services:
        currently_serving = (
            db.query(TokenRecord)
            .filter(TokenRecord.service_id == s_id, TokenRecord.status == "serving")
            .first()
        )

        waiting_list = (
            db.query(TokenRecord)
            .filter(TokenRecord.service_id == s_id, TokenRecord.status == "waiting")
            .order_by(TokenRecord.sequence.asc())
            .all()
        )

        completed_count = (
            db.query(TokenRecord)
            .filter(TokenRecord.service_id == s_id, TokenRecord.status == "completed")
            .count()
        )

        overview[s_id] = {
            "currently_serving": {
                "token_number": currently_serving.token_number,
                "service_option": currently_serving.service_option,
                "served_at": currently_serving.served_at,
            } if currently_serving else None,
            "waiting_count": len(waiting_list),
            "completed_today": completed_count,
            "waiting_tokens": [
                {
                    "token_number": t.token_number,
                    "sequence": t.sequence,
                    "service_option": t.service_option,
                    "estimated_time": t.estimated_time,
                    "created_at": t.created_at,
                }
                for t in waiting_list
            ],
        }

    return overview


# =========================
# START SERVING (STAFF ACTION)
# =========================

@router.post("/{service_id}/start-serving", response_model=AdminActionResponse)
def start_serving_next(service_id: str, db: Session = Depends(get_db)):
    """
    Staff clicks 'Start Serving' on dashboard.
    Moves the next student in line from waiting -> serving.
    """
    service_id = service_id.lower()

    # Find next waiting student
    next_token = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == service_id, TokenRecord.status == "waiting")
        .order_by(TokenRecord.sequence.asc())
        .first()
    )

    if not next_token:
        raise HTTPException(status_code=400, detail="No students currently waiting in queue.")

    next_token.status = "serving"
    next_token.served_at = datetime.utcnow()
    db.commit()

    # Recalculate queue
    recalculate_service_queue(db, service_id)

    remaining = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == service_id, TokenRecord.status == "waiting")
        .count()
    )

    return AdminActionResponse(
        message=f"Now serving token {next_token.token_number}",
        service_id=service_id,
        token_number=next_token.token_number,
        remaining_waiting_count=remaining,
    )


# =========================
# COMPLETE (STAFF ACTION)
# =========================

@router.post("/{service_id}/complete", response_model=AdminActionResponse)
def complete_current_token(service_id: str, db: Session = Depends(get_db)):
    """
    Staff finishes the student's work and clicks 'Complete'.
    Marks serving token completed, queue count decreases, and backend recalculates next positions.
    """
    service_id = service_id.lower()

    serving_token = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == service_id, TokenRecord.status == "serving")
        .first()
    )

    if not serving_token:
        # Fallback: complete earliest waiting token if none marked serving
        serving_token = (
            db.query(TokenRecord)
            .filter(TokenRecord.service_id == service_id, TokenRecord.status == "waiting")
            .order_by(TokenRecord.sequence.asc())
            .first()
        )

    if not serving_token:
        raise HTTPException(status_code=400, detail="No active or serving token found to complete.")

    serving_token.status = "completed"
    serving_token.completed_at = datetime.utcnow()
    db.commit()

    # Automatically recalculate positions and estimated times
    recalculate_service_queue(db, service_id)

    remaining = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == service_id, TokenRecord.status == "waiting")
        .count()
    )

    return AdminActionResponse(
        message=f"Completed token {serving_token.token_number}. Queue recalculated.",
        service_id=service_id,
        token_number=serving_token.token_number,
        remaining_waiting_count=remaining,
    )


# =========================
# RESET QUEUE (FOR TESTING / NEW DAY)
# =========================

@router.post("/{service_id}/reset")
def reset_queue(service_id: str, db: Session = Depends(get_db)):
    """
    Clears all active tokens for a service to allow fresh testing.
    If service_id is 'all', clears all tokens across all services.
    """
    service_id = service_id.lower()
    if service_id == "all":
        db.query(TokenRecord).delete()
    else:
        db.query(TokenRecord).filter(TokenRecord.service_id == service_id).delete()
    db.commit()

    return {"message": f"Queue for {service_id} has been reset."}
