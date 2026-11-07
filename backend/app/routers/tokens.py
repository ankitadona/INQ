from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import ServiceQueue, TokenRecord
from app.schemas.schemas import (
    CafeTokenRequest,
    DeanTokenRequest,
    PrintingTokenRequest,
    TokenResponse,
    TokenStatusUpdate,
)
from app.utils.queue_helpers import calculate_estimated_time, generate_token_number

router = APIRouter(prefix="/tokens", tags=["Tokens"])


def _get_people_ahead(db: Session, token: TokenRecord) -> int:
    """
    Counts how many tokens are in 'waiting' status with a sequence number lower than this token.
    """
    if token.status != "waiting":
        return 0

    return (
        db.query(TokenRecord)
        .filter(
            TokenRecord.service_id == token.service_id,
            TokenRecord.status == "waiting",
            TokenRecord.sequence < token.sequence,
        )
        .count()
    )


# =========================
# DEAN OFFICE QUEUE
# =========================

@router.post("/dean", response_model=TokenResponse)
def join_dean_queue(req: DeanTokenRequest, db: Session = Depends(get_db)):
    """
    Issue a new Dean Office token (e.g., D-27).
    """
    token_str, seq = generate_token_number(db, "dean", "D")

    waiting_count = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "dean", TokenRecord.status == "waiting")
        .count()
    )

    service_record = db.query(ServiceQueue).filter(ServiceQueue.id == "dean").first()
    avg_dur = service_record.avg_duration_minutes if service_record else 3
    est_time = calculate_estimated_time("dean", waiting_count + 1, avg_dur)

    record = TokenRecord(
        service_id="dean",
        token_number=token_str,
        sequence=seq,
        status="waiting",
        service_option=req.service_option,
        meta_info={"service_option": req.service_option},
        estimated_time=est_time,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return TokenResponse(
        id=record.id,
        token_number=record.token_number,
        service_id=record.service_id,
        people_ahead=waiting_count,
        estimated_time=record.estimated_time,
        status=record.status,
        created_at=record.created_at,
        meta_info=record.meta_info,
    )


# =========================
# PRINTING SHOP QUEUE
# =========================

@router.post("/printing", response_model=TokenResponse)
def join_printing_queue(req: PrintingTokenRequest, db: Session = Depends(get_db)):
    """
    Issue a new Printing Shop token (e.g., P-34).
    """
    token_str, seq = generate_token_number(db, "printing", "P")

    waiting_count = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "printing", TokenRecord.status == "waiting")
        .count()
    )

    service_record = db.query(ServiceQueue).filter(ServiceQueue.id == "printing").first()
    avg_dur = service_record.avg_duration_minutes if service_record else 4

    # Calculate extra time based on copies/pages if custom
    extra_minutes = 1 if req.colour == "Colour" else 0
    est_time = calculate_estimated_time("printing", waiting_count + 1, avg_dur + extra_minutes)

    record = TokenRecord(
        service_id="printing",
        token_number=token_str,
        sequence=seq,
        status="waiting",
        service_option="Print Job",
        meta_info=req.model_dump(),
        estimated_time=est_time,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return TokenResponse(
        id=record.id,
        token_number=record.token_number,
        service_id=record.service_id,
        people_ahead=waiting_count,
        estimated_time=record.estimated_time,
        status=record.status,
        created_at=record.created_at,
        meta_info=record.meta_info,
    )


# =========================
# CAMPUS CAFÉ QUEUE
# =========================

@router.post("/cafe", response_model=TokenResponse)
def join_cafe_queue(req: CafeTokenRequest, db: Session = Depends(get_db)):
    """
    Issue a new Campus Café order token (e.g., C-18).
    """
    token_str, seq = generate_token_number(db, "cafe", "C")

    waiting_count = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "cafe", TokenRecord.status == "waiting")
        .count()
    )

    service_record = db.query(ServiceQueue).filter(ServiceQueue.id == "cafe").first()
    avg_dur = service_record.avg_duration_minutes if service_record else 5
    est_time = calculate_estimated_time("cafe", waiting_count + 1, avg_dur)

    record = TokenRecord(
        service_id="cafe",
        token_number=token_str,
        sequence=seq,
        status="waiting",
        service_option="Café Order",
        meta_info=req.model_dump(),
        estimated_time=est_time,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return TokenResponse(
        id=record.id,
        token_number=record.token_number,
        service_id=record.service_id,
        people_ahead=waiting_count,
        estimated_time=record.estimated_time,
        status=record.status,
        created_at=record.created_at,
        meta_info=record.meta_info,
    )


# =========================
# TOKEN STATUS & TRACKING
# =========================

@router.get("/{token_number}", response_model=TokenResponse)
def get_token_status(token_number: str, db: Session = Depends(get_db)):
    """
    Fetch live status of a token, including real-time people/jobs ahead.
    """
    token_number = token_number.strip().upper()
    token = (
        db.query(TokenRecord)
        .filter(TokenRecord.token_number == token_number)
        .first()
    )

    if not token:
        raise HTTPException(status_code=404, detail=f"Token '{token_number}' not found")

    ahead = _get_people_ahead(db, token)

    return TokenResponse(
        id=token.id,
        token_number=token.token_number,
        service_id=token.service_id,
        people_ahead=ahead,
        estimated_time=token.estimated_time or "Now",
        status=token.status,
        created_at=token.created_at,
        meta_info=token.meta_info,
    )


@router.patch("/{token_number}/status", response_model=TokenResponse)
def update_token_status(
    token_number: str,
    update: TokenStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Operator endpoint: call next token ('serving'), complete ('completed'), or cancel ('cancelled').
    """
    token_number = token_number.strip().upper()
    token = (
        db.query(TokenRecord)
        .filter(TokenRecord.token_number == token_number)
        .first()
    )

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    token.status = update.status.lower()
    if token.status in ["completed", "cancelled"]:
        token.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(token)

    ahead = _get_people_ahead(db, token)

    return TokenResponse(
        id=token.id,
        token_number=token.token_number,
        service_id=token.service_id,
        people_ahead=ahead,
        estimated_time=token.estimated_time or "Completed",
        status=token.status,
        created_at=token.created_at,
        meta_info=token.meta_info,
    )
