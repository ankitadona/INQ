from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import ServiceQueue, TokenRecord
from app.schemas.schemas import PrintingTokenRequest, TokenResponse
from app.utils.queue_helpers import (
    estimate_printing_time,
    generate_token_number,
    get_crowd_status,
)

router = APIRouter(prefix="/printing", tags=["Printing Shop"])


@router.get("/status")
def get_printing_status(db: Session = Depends(get_db)):
    """
    Returns live Printing Shop queue count, crowd status, and estimated readiness time.
    """
    waiting_count = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "printing", TokenRecord.status == "waiting")
        .count()
    )

    serving_token = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "printing", TokenRecord.status == "serving")
        .first()
    )

    crowd_text, crowd_class = get_crowd_status("printing", waiting_count)
    wait_mins, est_reach_time = estimate_printing_time(waiting_count)

    return {
        "service": "printing",
        "name": "Printing Shop",
        "waiting_jobs_count": waiting_count,
        "crowd_status": crowd_text,
        "crowd_class": crowd_class,
        "currently_printing": serving_token.token_number if serving_token else None,
        "estimated_minutes_to_reach": wait_mins,
        "estimated_time_to_reach": est_reach_time,
    }


@router.post("/token", response_model=TokenResponse)
def generate_printing_token(req: PrintingTokenRequest, db: Session = Depends(get_db)):
    """
    1. Student takes a printing token.
    2. Backend checks how many students/jobs are ahead.
    3. Backend estimates how long those will take.
    4. Student sees an estimated time to reach the printing shop.
    """
    token_str, seq = generate_token_number(db, "printing", "P")

    waiting_count = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "printing", TokenRecord.status == "waiting")
        .count()
    )

    is_colour = (req.colour.lower() == "colour")
    wait_mins, est_reach_time = estimate_printing_time(
        jobs_ahead=waiting_count,
        copies=req.copies,
        is_colour=is_colour,
    )

    record = TokenRecord(
        service_id="printing",
        token_number=token_str,
        sequence=seq,
        status="waiting",
        service_option=f"{req.pages} ({req.colour})",
        meta_info=req.model_dump(),
        estimated_wait_minutes=wait_mins,
        estimated_time=est_reach_time,
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
