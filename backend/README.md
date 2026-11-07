# INQ — Campus Queue Management Backend

FastAPI and PostgreSQL/SQLAlchemy backend for the INQ campus queue system at VSSUT.

---

## 🛠 Tech Stack

- **Framework:** FastAPI
- **Server:** Uvicorn
- **ORM / Database:** SQLAlchemy (supports SQLite for instant local dev & PostgreSQL for production)
- **Validation:** Pydantic v2
- **Driver:** `psycopg` (v3)

---

## 🚀 Getting Started

### 1. Set Up Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

By default, `DATABASE_URL=sqlite:///./inq.db` allows immediate plug-and-play testing without any external setup.

To switch to **PostgreSQL**:
```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/inq_db
```

### 4. Run the Server

```bash
python run.py
```
Or with uvicorn directly:
```bash
uvicorn app.main:app --reload --port 8000
```

The server will start at **http://127.0.0.1:8000**.
Interactive API Docs (Swagger): **http://127.0.0.1:8000/docs**

---

## 📡 API Reference

### 1. Queues & Live Status

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/queues/status` | Live counts, crowd badges, and estimated times for Dean, Printing, and Café |
| `GET` | `/api/queues/{service_id}` | Details for a single queue (`dean`, `printing`, `cafe`) |

**Sample response (`GET /api/queues/status`):**
```json
{
  "dean": {
    "service": "dean",
    "name": "Dean Office",
    "count": 4,
    "estimated_time": "10:35 AM",
    "status_text": "Low Crowd",
    "status_class": "status-low",
    "is_open": true
  },
  "printing": {
    "service": "printing",
    "name": "Printing Shop",
    "count": 11,
    "estimated_time": "11:20 AM",
    "status_text": "Busy",
    "status_class": "status-medium",
    "is_open": true
  },
  "cafe": {
    "service": "cafe",
    "name": "Campus Café",
    "count": 7,
    "estimated_time": "9:00–9:05 AM",
    "status_text": "Moderate",
    "status_class": "status-medium",
    "is_open": true
  }
}
```

---

### 2. Token Generation & Tracking

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/tokens/dean` | Issue a Dean Office token (`D-XX`) |
| `POST` | `/api/tokens/printing` | Submit print configuration and get a token (`P-XX`) |
| `POST` | `/api/tokens/cafe` | Place order and receive a café token (`C-XX`) |
| `GET` | `/api/tokens/{token_number}` | Track real-time position and people ahead |
| `PATCH` | `/api/tokens/{token_number}/status` | Operator updates status (`serving`, `completed`, `cancelled`) |

**Join Dean Queue Example:**
```bash
curl -X POST http://127.0.0.1:8000/api/tokens/dean \
  -H "Content-Type: application/json" \
  -d '{"service_option": "Document Verification"}'
```

**Response:**
```json
{
  "id": 5,
  "token_number": "D-05",
  "service_id": "dean",
  "people_ahead": 4,
  "estimated_time": "10:47 AM",
  "status": "waiting",
  "created_at": "2026-11-05T01:50:00"
}
```
