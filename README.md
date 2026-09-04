# YojanaSetu - Backend & Rules Engine

Backend service and central deterministic eligibility engine for **YojanaSetu** (AI-assisted Government Scheme Discovery & Application Guidance Platform).

---

## 🛠 Tech Stack

- **Runtime & Language:** Python 3.10+
- **Framework:** FastAPI
- **Database & Storage:** PostgreSQL / Supabase
- **Data Validation:** Pydantic v2
- **Testing:** Pytest & HTTPX

---

## 📂 Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI application entrypoint & middleware setup
│   ├── api/             # API route controllers & router registration
│   ├── models/          # Database models (PostgreSQL / Supabase ORM entities)
│   ├── schemas/         # Pydantic schemas (Request/Response data contracts)
│   ├── services/        # Business logic layer (Profile, Scheme, Ranking orchestration)
│   ├── rules/           # Deterministic eligibility engine & reason codes
│   ├── db/              # Database connection, Supabase client & session management
│   ├── core/            # App settings, configuration & environment variables
│   └── tests/           # Automated test suite (unit and integration tests)
├── data/                # Scheme seed records, rule configurations & tutorial assets
├── .env.example         # Template for required environment variables
├── .gitignore           # Git ignore rules for Python, virtualenvs & secrets
├── requirements.txt     # Python project dependencies
└── README.md            # Backend documentation & guidelines
```

---

## 🎯 Backend Responsibilities (Member 2)

As outlined in the YojanaSetu blueprint:
1. **User / Profile Management:** Ingestion and retrieval of citizen profile attributes.
2. **Scheme Management:** Canonical scheme retrieval, metadata handling, and catalog endpoints.
3. **Eligibility Engine:** Pure, deterministic rule evaluation (Eligible / Potentially Eligible / Not Eligible).
4. **Explainability & Reason Codes:** Transparent pass/fail explanations mapped to user inputs.
5. **Recommendation & Ranking:** Profile-to-scheme scoring and relevance ordering.
6. **Database Interactions:** Secure persistence with Supabase / PostgreSQL.
7. **Unified Backend Gateway:** Single source of truth serving Web, AI/Search, and WhatsApp channels.

---

## 🚀 Getting Started

### 1. Clone & Setup Virtual Environment
```bash
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Update .env with your PostgreSQL / Supabase credentials
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`