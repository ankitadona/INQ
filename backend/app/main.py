from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine, SessionLocal
from app.models.models import AdminUser, MenuItem, ServiceQueue, TokenRecord
from app.routers import (
    admin_router,
    cafe_router,
    dean_router,
    printing_router,
    queues_router,
    tokens_router,
)
from app.utils.queue_helpers import hash_password


def init_database():
    """
    Creates tables and seeds initial realistic demo data if fresh.
    """
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if queues exist
        if db.query(ServiceQueue).count() == 0:
            db.add_all([
                ServiceQueue(
                    id="dean",
                    name="Dean Office",
                    prefix="D",
                    avg_duration_minutes=3,
                    service_hours_str="9:00 AM – 1:00 PM & 3:00 PM – 5:00 PM",
                    is_open=True,
                ),
                ServiceQueue(
                    id="printing",
                    name="Printing Shop",
                    prefix="P",
                    avg_duration_minutes=4,
                    service_hours_str="8:30 AM – 8:00 PM",
                    is_open=True,
                ),
                ServiceQueue(
                    id="cafe",
                    name="Campus Café",
                    prefix="C",
                    avg_duration_minutes=5,
                    service_hours_str="8:00 AM – 9:00 PM",
                    is_open=True,
                ),
            ])
            db.commit()

        # Seed admin users
        if db.query(AdminUser).count() == 0:
            db.add_all([
                AdminUser(username="dean", hashed_password=hash_password("dean123"), role="dean_staff", department="dean"),
                AdminUser(username="printing", hashed_password=hash_password("print123"), role="printing_staff", department="printing"),
                AdminUser(username="cafe", hashed_password=hash_password("cafe123"), role="cafe_staff", department="cafe"),
                AdminUser(username="admin", hashed_password=hash_password("admin123"), role="super_admin", department="all"),
            ])
            db.commit()

        # Seed café menu
        if db.query(MenuItem).count() == 0:
            db.add_all([
                MenuItem(name="Cold Coffee", price=25, prep_time_minutes=3),
                MenuItem(name="Cold Coffee + Ice Cream", price=40, prep_time_minutes=4),
                MenuItem(name="KitKat Shake", price=40, prep_time_minutes=5),
                MenuItem(name="Oreo Shake", price=40, prep_time_minutes=5),
                MenuItem(name="Veg Patties", price=15, prep_time_minutes=2),
                MenuItem(name="Paneer Patties", price=20, prep_time_minutes=2),
                MenuItem(name="Cheese Patties", price=25, prep_time_minutes=3),
                MenuItem(name="Sandwich", price=30, prep_time_minutes=5),
                MenuItem(name="Cheese Sandwich", price=40, prep_time_minutes=5),
                MenuItem(name="Grilled Sandwich", price=45, prep_time_minutes=6),
            ])
            db.commit()

        # Seed initial demo tokens if database is newly initialized
        if db.query(TokenRecord).count() == 0:
            # 4 students waiting at Dean
            for i in range(1, 5):
                db.add(TokenRecord(
                    service_id="dean",
                    token_number=f"D-{i:03d}",
                    sequence=i,
                    status="waiting",
                    service_option="Document Verification",
                    estimated_time="10:35 AM",
                    estimated_wait_minutes=i * 3,
                ))

            # 11 jobs ahead at Printing
            for i in range(1, 12):
                db.add(TokenRecord(
                    service_id="printing",
                    token_number=f"P-{i:03d}",
                    sequence=i,
                    status="waiting",
                    service_option="Print Job",
                    estimated_time="11:20 AM",
                    estimated_wait_minutes=5 + i,
                ))

            # 7 orders at Café
            for i in range(1, 8):
                db.add(TokenRecord(
                    service_id="cafe",
                    token_number=f"C-{i:03d}",
                    sequence=i,
                    status="waiting",
                    service_option="Café Order",
                    estimated_time="9:00–9:05 AM",
                    estimated_wait_minutes=8 + i * 2,
                ))

            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount All API Routers
app.include_router(queues_router, prefix=settings.API_V1_PREFIX)
app.include_router(dean_router, prefix=settings.API_V1_PREFIX)
app.include_router(printing_router, prefix=settings.API_V1_PREFIX)
app.include_router(cafe_router, prefix=settings.API_V1_PREFIX)
app.include_router(tokens_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "docs": "/docs",
        "endpoints": {
            "queue_status": f"{settings.API_V1_PREFIX}/queues/status",
            "dean": f"{settings.API_V1_PREFIX}/dean",
            "printing": f"{settings.API_V1_PREFIX}/printing",
            "cafe": f"{settings.API_V1_PREFIX}/cafe",
            "tokens": f"{settings.API_V1_PREFIX}/tokens",
            "admin": f"{settings.API_V1_PREFIX}/admin",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
