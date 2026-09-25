# KameraPh (PhotoBulk) — AI Academic Portrait & Regalia Platform

[![CI Pipeline](https://github.com/Ben010618/PhotoBulk/actions/workflows/ci.yml/badge.svg)](https://github.com/Ben010618/PhotoBulk/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61dafb.svg)](https://react.dev/)
[![Compliance](https://img.shields.io/badge/Compliance-RA%2010173%20(DPA)-darkgreen.svg)](PRIVACY_AND_COMPLIANCE_RA10173.md)

**KameraPh** is an AI-powered portrait enhancement and batch processing platform engineered specifically for high-volume Philippine graduation pictorials, school yearbooks, and board examination IDs.

---

## Key Features

1. **Academic Regalia & Toga Preservation**
   - True neural matting via `rembg` (U2Net ONNX) with GrabCut fallback.
   - Preserves mortarboards, tassels, academic hood folds, honor cords, and indigenous textiles (UP Sablay, Barong Tagalog).

2. **Morena Skin Tone Protection (Zero Bleaching)**
   - Calibrated in CIELAB color space ensuring melanin brightness drift does not exceed $\Delta L^* \le 3.5$.
   - Eliminates artificial whitewashing common in global retouching models.

3. **Official Philippine ID & Board Exam Standards**
   - **DFA Passport & PRC Board Exam Crop:** Automatic 600×600 px (1:1 aspect ratio) centered crop conforming to PRC and DFA biometric guidelines (head height between 70% and 80%).
   - **8R Stage Frame:** 4:5 aspect ratio yearbook print standard.
   - **Multi-Student Gang Sheet Generation:** Automatic 300 DPI lab print sheets with student identification.

4. **Multi-Tenant Studio Isolation & Security**
   - Row-Level Security (RLS) policies isolating photos, batches, and transactions per studio.
   - Server-checked session tokens (HMAC-SHA256) for all admin operations (`/api/admin/*`).
   - PayMongo webhook signature verification (HMAC-SHA256) preventing replay attacks and credit spoofing.
   - Strict CORS whitelist and path traversal sanitization for export filenames.

5. **Philippine Data Privacy Act (RA 10173) Governance**
   - Built-in parental consent tracking for minors.
   - Automated 90-day retention purge protocol and Right to Erasure handling.
   - Full governance documentation in [`PRIVACY_AND_COMPLIANCE_RA10173.md`](file:///c:/Users/USER/OneDrive%20-%20Department%20of%20Education/Desktop/PhotoBulk/PRIVACY_AND_COMPLIANCE_RA10173.md).

---

## System Architecture

```
┌────────────────────────────────────────────────────────┐
│              Browser Client (React 19 + Vite)          │
│   Comparison Slider | Filmstrip Queue | Studio Sliders │
└───────────────────────────┬────────────────────────────┘
                            │ REST / JSON (Streaming URLs)
┌───────────────────────────▼────────────────────────────┐
│                  Nginx Reverse Proxy                   │
│          SSL/TLS | Gzip | CSP & Security Headers       │
└───────────────────────────┬────────────────────────────┘
                            │ Port 8000
┌───────────────────────────▼────────────────────────────┐
│                   FastAPI Backend                      │
│     Auth & Sessions  │ Credit Checks │ Upload Limits   │
└───────┬───────────────────┬───────────────────┬────────┘
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
│ AI Vision      │  │ Storage & DB   │  │ Payment Engine │
│ • rembg U2Net  │  │ • SQLite / PG  │  │ • PayMongo     │
│ • YuNet Faces  │  │ • RLS Policies │  │ • HMAC-SHA256  │
│ • OpenCV LAB   │  │ • Cloudflare R2│  │ • GCash/Maya   │
│ • Gemini 2.5   │  │ • 90-Day Purge │  │ • 1 Credit/Pic │
└────────────────┘  └────────────────┘  └────────────────┘
```

---

## Environment Configuration

Create a `.env` file in the root directory based on `.env.example`:

```bash
cp .env.example .env
```

### Critical Environment Variables

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini API key for photo quality appraisal | *(Required for AI analysis)* |
| `PAYMONGO_SECRET_KEY` | PayMongo secret API key | `sec_test_...` |
| `PAYMONGO_WEBHOOK_SECRET` | PayMongo webhook signing secret | `whsec_...` |
| `SECRET_KEY` | Cryptographic secret for signing session tokens | *(Generate with `openssl rand -hex 32`)* |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed frontend domains | `http://localhost:5173,http://localhost:3000` |
| `DATABASE_URL` | Database connection string | `sqlite:///kameraph.db` or PostgreSQL |
| `R2_ENDPOINT_URL` | Cloudflare R2 S3 endpoint URL | `https://<account_id>.r2.cloudflarestorage.com` |
| `R2_ACCESS_KEY_ID` | Cloudflare R2 Access Key | *(Optional, for cloud storage)* |
| `R2_SECRET_ACCESS_KEY` | Cloudflare R2 Secret Access Key | *(Optional, for cloud storage)* |
| `R2_BUCKET_NAME` | Cloudflare R2 bucket name | `kameraph-portraits` |
| `MAX_UPLOAD_SIZE_MB` | Maximum single file upload size | `25` |
| `MAX_BATCH_UPLOAD_COUNT` | Maximum files per batch upload | `100` |

---

## Getting Started

### Prerequisites
- Python 3.11 or 3.13
- Node.js 18+ and npm
- (Optional) Docker & Docker Compose

### 1. Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt

# Initialize database and tables
python init_db.py

# Launch FastAPI server
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

## Docker Production Deployment

Run the complete production stack (Backend + Frontend + Nginx + SSL):

```bash
# Build and start services
docker-compose up --build -d

# Check status
docker-compose ps
```

---

## Database Backups

Run the zero-downtime online database backup script:

```bash
python backup_db.py
```

Backups are compressed with gzip, verified with `PRAGMA integrity_check`, stored in `backups/`, and automatically pruned past the 14-day retention window.

---

## Running the Automated Test Suite

Run the full automated test suite covering security, matting regression, color spaces, credit enforcement, and crops:

```bash
pytest tests/test_kamera_suite.py -v
```

All 12 tests validate:
- Row-Level Security (RLS) multi-tenant isolation
- Admin endpoint session protection
- PayMongo webhook signature verification & idempotency
- Cap, tassel, and gown matting retention
- Morena skin tone CIELAB preservation ($\Delta L^* \le 3.5$)
- DFA/PRC 600×600 2×2 crop dimensions
- Multi-face and zero-face review flagging
- Zero-credit 402 blocking & credit deduction
- Multi-student batch gang sheet PDF rendering
- Filename sanitization against path traversal
- URL image streaming

---

## License & Compliance

Proprietary software developed for Philippine photographic studios. Compliant with Republic Act No. 10173 (Philippine Data Privacy Act of 2012).
