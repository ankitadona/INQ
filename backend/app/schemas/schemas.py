from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =========================
# QUEUE SCHEMAS
# =========================

class QueueStatus(BaseModel):
    service: str
    name: str
    count: int
    estimated_time: str
    status_text: str
    status_class: str
    is_open: bool
    service_hours: Optional[str] = None


class GlobalStatusResponse(BaseModel):
    dean: QueueStatus
    printing: QueueStatus
    cafe: QueueStatus


# =========================
# TOKEN REQUEST SCHEMAS
# =========================

class DeanTokenRequest(BaseModel):
    service_option: str = Field(..., description="Selected service option (e.g. Document Verification)")


class PrintingTokenRequest(BaseModel):
    file_name: Optional[str] = "document.pdf"
    paper_size: str = "A4"
    colour: str = "Black & White"
    sides: str = "Single-sided"
    pages: str = "All pages"
    copies: int = 1


class OrderItem(BaseModel):
    name: str
    quantity: int = 1
    price: Optional[int] = None


class CafeTokenRequest(BaseModel):
    items: List[OrderItem] = Field(default_factory=list)
    other_item: Optional[str] = None
    notes: Optional[str] = None


# =========================
# TOKEN RESPONSE SCHEMAS
# =========================

class TokenResponse(BaseModel):
    id: int
    token_number: str
    service_id: str
    people_ahead: int
    estimated_wait_minutes: Optional[int] = None
    estimated_time: str
    status: str
    created_at: datetime
    service_option: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TokenStatusUpdate(BaseModel):
    status: str


# =========================
# ADMIN & AUTH SCHEMAS
# =========================

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str
    department: str


class AdminActionResponse(BaseModel):
    message: str
    service_id: str
    token_number: Optional[str] = None
    remaining_waiting_count: int
