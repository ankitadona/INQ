from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import MenuItem, ServiceQueue, TokenRecord
from app.schemas.schemas import CafeTokenRequest, TokenResponse
from app.utils.queue_helpers import (
    estimate_cafe_prep_time,
    generate_token_number,
    get_crowd_status,
)

router = APIRouter(prefix="/cafe", tags=["Campus Café"])


def seed_menu_if_empty(db: Session):
    default_menu = [
        {"name": "Cold Coffee", "price": 25, "prep_time_minutes": 3},
        {"name": "Cold Coffee + Ice Cream", "price": 40, "prep_time_minutes": 4},
        {"name": "KitKat Shake", "price": 40, "prep_time_minutes": 5},
        {"name": "Oreo Shake", "price": 40, "prep_time_minutes": 5},
        {"name": "Veg Patties", "price": 15, "prep_time_minutes": 2},
        {"name": "Paneer Patties", "price": 20, "prep_time_minutes": 2},
        {"name": "Cheese Patties", "price": 25, "prep_time_minutes": 3},
        {"name": "Sandwich", "price": 30, "prep_time_minutes": 5},
        {"name": "Cheese Sandwich", "price": 40, "prep_time_minutes": 5},
        {"name": "Grilled Sandwich", "price": 45, "prep_time_minutes": 6},
    ]

    if db.query(MenuItem).count() == 0:
        for m in default_menu:
            db.add(MenuItem(**m))
        db.commit()


@router.get("/menu")
def get_cafe_menu(db: Session = Depends(get_db)):
    """
    Returns available café items with prices and preparation times.
    """
    seed_menu_if_empty(db)
    return db.query(MenuItem).filter(MenuItem.is_available == True).all()


@router.get("/status")
def get_cafe_status(db: Session = Depends(get_db)):
    """
    Returns live Café queue count, crowd status, and pickup readiness window.
    """
    waiting_count = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "cafe", TokenRecord.status == "waiting")
        .count()
    )

    serving_token = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "cafe", TokenRecord.status == "serving")
        .first()
    )

    crowd_text, crowd_class = get_crowd_status("cafe", waiting_count)
    wait_mins, est_window = estimate_cafe_prep_time(waiting_count, [])

    return {
        "service": "cafe",
        "name": "Campus Café",
        "orders_ahead": waiting_count,
        "crowd_status": crowd_text,
        "crowd_class": crowd_class,
        "currently_preparing": serving_token.token_number if serving_token else None,
        "estimated_wait_minutes": wait_mins,
        "estimated_pickup_window": est_window,
    }


@router.post("/order", response_model=TokenResponse)
def place_cafe_order(req: CafeTokenRequest, db: Session = Depends(get_db)):
    """
    1. Student selects food items from the menu.
    2. Places order and gets token (e.g. C-108).
    3. Backend estimates prep time based on orders ahead + selected items.
    4. Student sees estimated time to reach the café and collect the order.
    """
    token_str, seq = generate_token_number(db, "cafe", "C")

    waiting_count = (
        db.query(TokenRecord)
        .filter(TokenRecord.service_id == "cafe", TokenRecord.status == "waiting")
        .count()
    )

    items_dict_list = [item.model_dump() for item in req.items]
    wait_mins, est_window = estimate_cafe_prep_time(waiting_count, items_dict_list)

    # Format brief summary of items
    summary_parts = [f"{it.quantity}x {it.name}" for it in req.items[:2]]
    if req.other_item:
        summary_parts.append(req.other_item)
    summary_text = ", ".join(summary_parts) if summary_parts else "Café Order"

    record = TokenRecord(
        service_id="cafe",
        token_number=token_str,
        sequence=seq,
        status="waiting",
        service_option=summary_text,
        meta_info={
            "items": items_dict_list,
            "other_item": req.other_item,
            "notes": req.notes,
        },
        estimated_wait_minutes=wait_mins,
        estimated_time=est_window,
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
