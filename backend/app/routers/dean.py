from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import ServiceQueue, TokenRecord
from app.schemas.schemas import DeanTokenRequest, TokenResponse
from app.utils.queue_helpers import (
    estimate_dean_wait_time,
    generate_token_number,
    get_crowd_status,
    is_dean_office_open,
)

router = APIRouter(prefix="/dean", tags=["Dean Office"])


@router.get("/status")
def get_dean_status(db: Session = Depends(get_db)):
    """
    Returns live Dean office queue status, crowd badge, and office service hours.
    """
    is_open, hours_str = is_dean_office_open()

    waiting_count = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "dean", TokenRecord.status == "waiting")
        .count()
    )

    serving_token = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "dean", TokenRecord.status == "serving")
        .first()
    )

    crowd_text, crowd_class = get_crowd_status("dean", waiting_count)
    service_rec = db.query(ServiceQueue).filter(ServiceQueue.id == "dean").first()
    avg_dur = service_rec.avg_duration_minutes if service_rec else 3

    wait_mins, est_turn = estimate_dean_wait_time(waiting_count, avg_dur)

    return {
        "service": "dean",
        "name": "Dean Office",
        "service_hours": hours_str,
        "is_open": is_open,
        "waiting_count": waiting_count,
        "crowd_status": crowd_text,
        "crowd_class": crowd_class,
        "currently_serving": serving_token.token_number if serving_token else None,
        "estimated_wait_minutes": wait_mins,
        "estimated_next_turn": est_turn,
    }


@router.post("/token", response_model=TokenResponse)
def generate_dean_token(req: DeanTokenRequest, db: Session = Depends(get_db)):
    """
    Student generates token for Dean Office (e.g. D-027).
    Queue count increases automatically.
    """
    token_str, seq = generate_token_number(db, "dean", "D")

    waiting_count = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "dean", TokenRecord.status == "waiting")
        .count()
    )

    service_rec = db.query(ServiceQueue).filter(ServiceQueue.id == "dean").first()
    avg_dur = service_rec.avg_duration_minutes if service_rec else 3

    wait_mins, est_turn = estimate_dean_wait_time(waiting_count + 1, avg_dur)

    record = TokenRecord(
        service_id="dean",
        token_number=token_str,
        sequence=seq,
        status="waiting",
        service_option=req.service_option,
        meta_info={"service_option": req.service_option},
        estimated_wait_minutes=wait_mins,
        estimated_time=est_turn,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return TokenResponse(
        id=record.id,
        token_number=record.token_number,
        service_id=record.service_id,
        people_ahead=waiting_count,
        estimated_wait_minutes=record.estimated_wait_minutes,
        estimated_time=record.estimated_time,
        status=record.status,
        created_at=record.created_at,
        service_option=record.service_option,
        meta_info=record.meta_info,
    )
