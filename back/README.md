#  Backend – Clothing Code Violation Detection API

## Overview
This backend provides a REST API for detecting clothing‑code violations from uploaded images.  
It is built with **FastAPI**, uses **Supabase (PostgreSQL)** as the database backend, and follows a clean modular architecture.

The system manages three core entities:

- **Images** – uploaded media stored and analyzed  
- **Violations** – detected rule breaches associated with an image  
- **Alerts** – notifications created when a violation requires escalation  

The backend is designed to be:

- modular  
- production‑ready  
- fully typed  
- easy to deploy with Docker  

---

##  Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI |
| Database | Supabase (PostgreSQL) |
| DB Access | asyncpg / custom utilities |
| Settings | Pydantic Settings |
| Image Handling | Pillow / custom file utils |
| Containerization | Docker |
| API Docs | Swagger / ReDoc |

---

##  Project Structure

```
back/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── detect.py        # Image upload + violation detection
│   │
│   ├── models/
│   │   ├── alertes.py             # Alert model
│   │   ├── images.py            # Image model
│   │   └── violations.py         # Violation model
│   │
│   ├── utils/
│   │   ├── database.py          # DB connection + queries
│   │   └── file_utils.py        # File saving, validation, cleanup
│   │
│   ├── config.py                # App settings (env-based)
│   └── main.py                  # FastAPI app entrypoint
│
├── requirements.txt
└── Dockerfile
```

---

##  Configuration

The backend uses environment variables loaded via `pydantic_settings`.

Create a `.env` file:

```
DATABASE_URL=your_supabase_postgres_url
APP_VERSION=1.0.0
DIRECT_URL=your_supabase_storage_url
DEBUG=True
UPLOAD_DIR=uploads
```

---

## ▶️ Running the Backend

### **Local (without Docker)**

1. Create a virtual environment:
```
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Start the server:
```
uvicorn app.main:app --reload
```

API available at:

- Swagger → `http://localhost:8000/docs`
- ReDoc → `http://localhost:8000/redoc`

---

##  Running with Docker

Build:

```
docker build -t backend .
```

Run:

```
docker run -p 8000:8000 --env-file .env backend
```

---

##  API Endpoints

### **POST /detect**
Upload an image and trigger:

- image storage  
- violation detection  
- violation creation  
- alert creation (if needed)  

**Request:**

```
POST /detect
Content-Type: multipart/form-data
file: <image>
```

**Response example:**

```json
{
  "image_id": 42,
  "violations": [
    {"type": "short_skirt", "confidence": 0.92}
  ],
  "alert_created": true
}
```

---

##  Data Models

### **Image**
Represents an uploaded media file.

Fields include:
- id  
- filename  
- path  
- upload timestamp  

### **Violation**
Represents a detected clothing‑code violation.

Fields include:
- id  
- image_id  
- violation_type  
- confidence score  

### **Alerte**
Represents a notification triggered by a violation.

Fields include:
- id  
- image_id  
- violation_id  
- severity  
- timestamp  

---

##  Testing

```
pytest
```

---

##  Deployment

Compatible with:

- Docker Compose  
- Render  
- Railway  
- Supabase Edge Functions (external API)  
- Any VM or container environment  

---

##  Notes

- All models map to existing Supabase tables.  
- No table creation occurs at runtime.  
- File uploads can be stored locally or via Supabase Storage.  
- Architecture is modular and easy to extend.

