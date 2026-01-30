<div align="center">

<img src="https://img.shields.io/badge/ClaimIQ-Kfz%20AI-1A56A0?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyTDIgN2wxMCA1IDEwLTV6TTIgMTdsOCA0IDgtNE0yIDEybDggNCA4LTQiLz48L3N2Zz4=" />

# ClaimIQ

### AI-powered Kfz claim analysis for German insurance brokers

**Upload a Schadensmeldung PDF → get a structured, decision-ready result in under 5 seconds.**

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Gemini](https://img.shields.io/badge/Gemini-AI-8E75B2?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/license-MIT-22C55E?style=flat-square)](LICENSE)

<br/>

[**Live Demo**](#quick-start) · [**API Docs**](http://localhost:8000/docs) · [**Report Bug**](mailto:afefischer@gmail.com) · [**Request Feature**](mailto:afefischer@gmail.com?subject=ClaimIQ%20Feature%20Request)

</div>

---

## What is ClaimIQ?

ClaimIQ automates the most tedious part of a German insurance broker's day — reading Kfz Schadensmeldungen and deciding what's missing before forwarding to the insurer.

**Without ClaimIQ:** 15–20 minutes per claim. Manual checklist. Easy to miss fields. Client callbacks.
**With ClaimIQ:** 5 seconds. Structured extraction. Readiness score. Action checklist. Shareable PDF.

```
PDF / Image
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  OCR Pipeline                                           │
│  Tesseract (deu+eng) ──→ confidence < 80%?             │
│                                  │ yes                  │
│                          Google Vision API              │
└─────────────────────────────────────────────────────────┘
    │  extracted text
    ▼
┌─────────────────────────────────────────────────────────┐
│  Gemini AI  (2 calls)                                   │
│  1. Extraction prompt  → structured Kfz fields          │
│  2. Scoring prompt     → readiness score + checklist    │
└─────────────────────────────────────────────────────────┘
    │
    ▼
Readiness Score · Breakdown · Flags · Checklist · PDF
```

---

## Features

| | Feature | Description |
|---|---|---|
| 🎯 | **Claim Readiness Score** | 0–100 score across 4 dimensions: completeness, consistency, fraud signals, documentation |
| 🤖 | **AI Field Extraction** | Gemini extracts all Kfz fields — Kennzeichen, Schadenshöhe, VSN, Unfallhergang, and more |
| ⚠️ | **Fraud Signal Detection** | Auto-flags German insurance fraud patterns: claim date = policy start, round amounts, late filing |
| 📋 | **Broker Action Checklist** | Interactive to-do: exactly what to request next, required vs optional, checkable in-app |
| 📄 | **Branded PDF Report** | One-click Schadensübersicht PDF — brokers send it to clients |
| 🌐 | **DE / EN UI** | Full German and English toggle, built for German brokers first |
| ⚡ | **Demo Mode** | No API keys needed — full UI flow works with realistic mock data |
| 📱 | **PWA** | Installable as a mobile app, works on broker smartphones |

---

## Tech Stack

### Backend
| Layer | Tech | Why |
|---|---|---|
| API | FastAPI + uvicorn | Async, typed, auto-docs |
| OCR | Tesseract 5 (deu/eng) + Google Vision fallback | Free-first, German language pack |
| AI | Google Gemini 1.5 Flash | Cost-efficient, strong German language |
| DB | SQLite (dev) / PostgreSQL (prod) | Zero-config dev, Neon free tier for prod |
| Storage | Local filesystem / Cloudflare R2 | No egress fees |
| PDF | ReportLab | Pure Python, no browser dependency |

### Frontend
| Layer | Tech | Why |
|---|---|---|
| Framework | Next.js 14 (App Router) | RSC, PWA, edge-ready |
| Styling | Tailwind CSS v3 JIT | Glassmorphism, custom animations |
| Language | TypeScript | End-to-end type safety with backend schemas |
| Fonts | Inter (Google Fonts) | Clean, readable, professional |

---

## Project Structure

```
ClaimIQ/
├── backend/
│   ├── .env.example              ← copy to .env and configure
│   ├── requirements.txt
│   └── app/
│       ├── main.py               ← FastAPI entry point
│       ├── core/config.py        ← settings, reads .env
│       ├── db/database.py        ← SQLAlchemy async engine
│       ├── models/claim.py       ← DB tables
│       ├── schemas/claim.py      ← Pydantic request / response models
│       ├── prompts/
│       │   └── kfz_prompts.py    ← German Kfz extraction + scoring prompts
│       ├── services/
│       │   ├── ocr_service.py    ← Tesseract + Google Vision fallback
│       │   ├── ai_service.py     ← Gemini + mock mode
│       │   ├── claim_service.py  ← pipeline orchestrator
│       │   ├── storage_service.py
│       │   └── pdf_service.py    ← branded PDF report
│       └── api/claims.py         ← REST endpoints
│
└── frontend/
    ├── tailwind.config.js
    └── src/
        ├── app/
        │   ├── layout.tsx        ← root layout + PWA meta
        │   ├── globals.css       ← glass, gradient-text, animations
        │   ├── landing/page.tsx  ← animated marketing landing page
        │   ├── upload/page.tsx   ← drag-and-drop upload
        │   └── result/[id]/      ← results with score + checklist
        ├── components/
        │   ├── ScoreGauge.tsx         ← animated circular dial
        │   ├── ScoreBreakdownPanel.tsx
        │   ├── FlagsPanel.tsx
        │   ├── ActionChecklist.tsx
        │   └── FeedbackModal.tsx
        └── lib/
            ├── api.ts            ← typed API client
            ├── i18n.ts           ← DE / EN translations
            └── utils.ts          ← helpers, score colors
```

---

## Quick Start

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Tesseract OCR | 5.x | See below |

**Install Tesseract with German language pack:**

```bash
# Windows — download installer (check "German (deu)" during install)
# https://github.com/UB-Mannheim/tesseract/wiki

# macOS
brew install tesseract tesseract-lang

# Linux
sudo apt install tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng
```

---

### 1 — Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Open `.env` and set:

```env
# Required on Windows — full path to tesseract binary
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe

# Optional — leave blank for Demo Mode (no API key needed)
GEMINI_API_KEY=

# Optional — enables Google Vision OCR fallback
GOOGLE_VISION_API_KEY=
```

> **Demo Mode** — if `GEMINI_API_KEY` is blank, ClaimIQ returns realistic mock data so you can test the entire UI without any API keys.

```bash
# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify at **http://localhost:8000/health** — you should see:
```json
{ "status": "ok", "mode": "mock" }
```

Interactive API docs: **http://localhost:8000/docs**

---

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

---

### 3 — Test the Flow

1. Go to **http://localhost:3000**
2. Drag and drop any PDF (a sample is included: `mock_kfz_schaden.pdf`)
3. Click **Schaden analysieren**
4. See the full results: score gauge → breakdown → flags → checklist → PDF download

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/claims/upload` | Upload document → full AI analysis |
| `GET` | `/api/v1/claims/{id}` | Fetch claim result |
| `POST` | `/api/v1/claims/{id}/feedback` | Submit broker correction |
| `GET` | `/api/v1/claims/{id}/pdf` | Download branded PDF report |
| `GET` | `/api/v1/claims/usage` | Usage stats for cost monitoring |
| `GET` | `/health` | Health + mode check |

Full interactive docs with request/response schemas at **http://localhost:8000/docs**

---

## Deployment

### Backend — Railway (~€5/month)

```bash
# 1. Push to GitHub
# 2. railway.app → New Project → from GitHub → select repo
# 3. Set env vars in Railway dashboard (same as .env)
# 4. Railway auto-deploys on every push
```

### Database — Neon (free PostgreSQL)

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host/claimiq
```

### File Storage — Cloudflare R2 (free, no egress)

```env
STORAGE_BACKEND=r2
R2_BUCKET_NAME=claimiq-uploads
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
```

### Frontend — Vercel (free)

```bash
# 1. Import GitHub repo at vercel.com
# 2. Set NEXT_PUBLIC_API_URL to your Railway backend URL
# 3. Deploy
```

---

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

---

## Cost at Scale

| Phase | Monthly Cost |
|---|---|
| Development (local) | **€0** |
| Live — Railway + free DB/storage | **~€5–10** |
| Growing — 100+ claims/day | **~€20–50** |

---

## Troubleshooting

**`TesseractNotFoundError` on Windows**
```env
# In backend/.env:
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe
```

**`No module named cv2`**
```bash
pip install opencv-python-headless
```

**`No module named fitz`**
```bash
pip install pymupdf
```

**Frontend can't reach backend**
```env
# In frontend/.env.local:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**CORS error**
```env
# In backend/.env:
APP_CORS_ORIGINS=http://localhost:3000
```

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

Built with precision for the German insurtech market.
**ClaimIQ** — from document to decision in seconds.

</div>
