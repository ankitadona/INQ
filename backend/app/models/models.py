from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String
from app.database import Base


class ServiceQueue(Base):
    __tablename__ = "service_queues"

    id = Column(String(50), primary_key=True, index=True)  # "dean", "printing", "cafe"
    name = Column(String(100), nullable=False)
    prefix = Column(String(10), nullable=False)  # "D", "P", "C"
    avg_duration_minutes = Column(Integer, default=3)
    service_hours_str = Column(String(150), default="9:00 AM – 1:00 PM & 3:00 PM – 5:00 PM")
    is_open = Column(Boolean, default=True)


class TokenRecord(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_id = Column(String(50), index=True, nullable=False)  # "dean", "printing", "cafe"
    token_number = Column(String(50), unique=True, index=True, nullable=False)
    sequence = Column(Integer, nullable=False)
    status = Column(String(30), default="waiting", index=True)  # waiting, serving, completed, cancelled
    service_option = Column(String(100), nullable=True)  # e.g., "Document Verification"
    meta_info = Column(JSON, nullable=True)  # print configs, cafe items, etc.
    estimated_wait_minutes = Column(Integer, default=5)
    estimated_time = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    served_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(50), default="staff")  # dean_staff, printing_staff, cafe_staff, admin
    department = Column(String(50), default="all")  # dean, printing, cafe, all


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)
    prep_time_minutes = Column(Integer, default=4)
    is_available = Column(Boolean, default=True)
