from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import ServiceQueue, TokenRecord
from app.schemas.schemas import GlobalStatusResponse, QueueStatus
from app.utils.queue_helpers import (
    calculate_estimated_time,
    get_crowd_status,
    is_dean_office_open,
)

router = APIRouter(prefix="/queues", tags=["Queues"])


def seed_services_if_empty(db: Session):
    default_services = [
        {
            "id": "dean",
            "name": "Dean Office",
            "prefix": "D",
            "avg_duration_minutes": 3,
            "service_hours_str": "9:00 AM – 1:00 PM & 3:00 PM – 5:00 PM",
        },
        {
            "id": "printing",
            "name": "Printing Shop",
            "prefix": "P",
            "avg_duration_minutes": 4,
            "service_hours_str": "8:30 AM – 8:00 PM",
        },
        {
            "id": "cafe",
            "name": "Campus Café",
            "prefix": "C",
            "avg_duration_minutes": 5,
            "service_hours_str": "8:00 AM – 9:00 PM",
        },
    ]

    for s in default_services:
        existing = db.query(ServiceQueue).filter(ServiceQueue.id == s["id"]).first()
        if not existing:
            db.add(ServiceQueue(**s))
    db.commit()


@router.get("/status", response_model=GlobalStatusResponse)
def get_all_queues_status(db: Session = Depends(get_db)):
    """
    Returns live crowd counts, estimated wait times, service hours, and crowd badges.
    """
    seed_services_if_empty(db)

    services = ["dean", "printing", "cafe"]
    status_map = {}

    for s_id in services:
        service_record = db.query(ServiceQueue).filter(ServiceQueue.id == s_id).first()
        waiting_count = (
            db.query(TokenRecord)
            .filter(TokenRecord.service_id == s_id, TokenRecord.status == "waiting")
            .count()
        )

        avg_dur = service_record.avg_duration_minutes if service_record else 3
        name = service_record.name if service_record else s_id.capitalize()
        hours_str = service_record.service_hours_str if service_record else None

        if s_id == "dean":
            is_open, dean_hours = is_dean_office_open()
            hours_str = dean_hours
        else:
            is_open = service_record.is_open if service_record else True

        text, badge_class = get_crowd_status(s_id, waiting_count)
        est_time = calculate_estimated_time(s_id, waiting_count, avg_dur)

        status_map[s_id] = QueueStatus(
            service=s_id,
            name=name,
            count=waiting_count,
            estimated_time=est_time,
            status_text=text,
            status_class=badge_class,
            is_open=is_open,
            service_hours=hours_str,
        )

    return GlobalStatusResponse(
        dean=status_map["dean"],
        printing=status_map["printing"],
        cafe=status_map["cafe"],
    )


@router.get("/{service_id}", response_model=QueueStatus)
def get_single_queue(service_id: str, db: Session = Depends(get_db)):
    """
    Returns live queue details for a single service.
    """
    service_id = service_id.lower()
    service_record = db.query(ServiceQueue).filter(ServiceQueue.id == service_id).first()
    if not service_record:
        raise HTTPException(status_code=404, detail="Service queue not found")

    waiting_count = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == service_id, TokenRecord.status == "waiting")
        .count()
    )

    hours_str = service_record.service_hours_str
    if service_id == "dean":
        is_open, hours_str = is_dean_office_open()
    else:
        is_open = service_record.is_open

    text, badge_class = get_crowd_status(service_id, waiting_count)
    est_time = calculate_estimated_time(service_id, waiting_count, service_record.avg_duration_minutes)

    return QueueStatus(
        service=service_id,
        name=service_record.name,
        count=waiting_count,
        estimated_time=est_time,
        status_text=text,
        status_class=badge_class,
        is_open=is_open,
        service_hours=hours_str,
    )
