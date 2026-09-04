# Mini Attendance Management System

A production-ready, clean-architecture backend foundation for an Attendance Management System built for a technical assessment.

---

## 1. Project Purpose

The Mini Attendance Management System is designed to manage employees, record daily attendance, track working hours, and enforce organizational business rules.

This repository currently contains the **modular monolith foundation**:
- Minimal FastAPI setup with health checking and root endpoints.
- Environment-based configuration using Pydantic Settings.
- Database layer with SQLAlchemy 2.0 and Alembic migration framework.
- Core security primitives (bcrypt password hashing, JWT creation/decoding).
- Docker and Docker Compose containerization for the backend and PostgreSQL.
- Automated testing suite with Pytest and HTTPX/TestClient.

---

## 2. Technology Stack

### Backend
- **Language**: Python 3.12+
- **Framework**: FastAPI
- **Database ORM**: SQLAlchemy 2.0
- **Database Driver**: Psycopg 3 (`psycopg[binary]`)
- **Database**: PostgreSQL 16
- **Schema & Validation**: Pydantic v2 & Pydantic Settings
- **Migrations**: Alembic
- **Security & Tokens**: Bcrypt, PyJWT
- **Testing**: Pytest, HTTPX

### Infrastructure & Tooling
- **Containerization**: Docker & Docker Compose
- **Server**: Uvicorn ASGI

### Frontend (Upcoming Phase)
- React, Vite, Axios, React Router, Tailwind CSS

---

## 3. Project Architecture

The backend follows a clean **Modular Monolith** architecture:

```text
attendance-management-system/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app initialization, middleware, endpoints
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # Pydantic BaseSettings loaded from env
│   │   │   ├── security.py      # Bcrypt hashing and JWT utilities
│   │   │   └── dependencies.py  # Session provider (get_db) and DI stubs
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py      # SQLAlchemy 2.0 engine, SessionLocal, DeclarativeBase
│   │   │   └── models/          # Entity models registry
│   │   │       └── __init__.py
│   │   │
│   │   ├── schemas/             # Pydantic request/response schemas (future)
│   │   │   └── __init__.py
│   │   │
│   │   ├── routers/             # API routes under /api/v1 (future)
│   │   │   └── __init__.py
│   │   │
│   │   └── services/            # Encapsulated business logic (future)
│   │       └── __init__.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py       # Health check and security unit tests
│   │
│   ├── alembic/                 # Alembic migration scripts and env.py
│   ├── alembic.ini              # Alembic configuration
│   ├── requirements.txt         # Pinned Python dependencies
│   ├── .env.example             # Template environment variables
│   ├── .gitignore
│   └── Dockerfile               # Production container image
│
├── frontend/                    # React frontend directory (future)
├── docker-compose.yml           # Backend and PostgreSQL composition
├── .gitignore
└── README.md
```

---

## 4. How to Run Locally (Without Docker)

### Prerequisites
- Python 3.12+
- PostgreSQL (or run only tests/mocked DB)

### 1. Set Up Virtual Environment & Dependencies
```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# On Windows PowerShell:
Copy-Item .env.example .env
# On macOS / Linux:
cp .env.example .env
```

### 3. Run the Development Server
```bash
# From backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 5. How to Run with Docker Compose

Ensure Docker and Docker Compose are installed and running on your host machine:

```bash
# Start backend and PostgreSQL containers in background
docker compose up -d --build

# View logs
docker compose logs -f

# Check health status
curl http://localhost:8000/health

# Stop containers
docker compose down
```

---

## 6. How to Run Tests

From the `backend` directory:

```bash
# Run test suite
pytest -v

# Run with output details
pytest -v -s
```
