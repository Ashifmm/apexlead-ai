# ⚡ ApexLead AI — AI-Powered Web Agency Lead Generation System

An intelligent, full-stack engine designed for web design and development agencies to discover high-value business leads, audit existing web presence, generate hyper-personalized website demos, and craft custom outreach across cold email and Instagram direct messages.

---

## 🧭 Project Roadmap & Incremental Stages

Following best engineering practices, this platform is engineered in modular, decoupled stages:

- [x] **Stage 1: Foundation (Current Release)**
  - Clean modular architecture (FastAPI backend + Next.js frontend + SQLite database)
  - Full Lead data model & Pydantic validation schemas
  - Complete RESTful CRUD API with filtering, pagination, and search
  - Real-time Pipeline Health and Aggregated Stats endpoints
  - Sleek modern Glassmorphic Dashboard with lead inspection, manual entry, status progression, and demo seeding
  - Environment variable isolation (`.env` / `.env.example`)
- [x] **Stage 2: AI Lead Scoring Engine** (Weighted scoring based on industry average order value, absence of website, or severe UX flaws)
- [x] **Stage 3: Automated Website Analyzer** (Headless audit of SSL, mobile responsiveness, Lighthouse speed scores, and UX critique)
- [x] **Stage 4: AI Outreach Generator** (Google Gemini 2.5 Flash pipeline drafting personalized cold emails & Instagram DMs)
- [x] **Stage 5 & 6: AI Website Demo Generator & Live Hosting** (Automated generation of multi-page Tailwind HTML website demos: Home, About, Services, Contact, with live preview & lead drawer integration)
- [ ] **Stage 7: Advanced Analytics & Conversion Tracking**
- [ ] **Stage 8: n8n Automation Workflows & Webhooks** (End-to-end autonomous discovery, enrichment, and outreach pipelines)

---

## 📁 Project Structure & Files Created

```
ai-web-agency-agent/
├── .env.example                     # Global environment template (GEMINI_API_KEY, Database URL)
├── .gitignore                       # Git ignore rules for Python, Next.js, SQLite, and venv
├── README.md                        # Documentation, architecture, and run guides
│
├── backend/                         # FastAPI Python Backend
│   ├── .env.example                 # Backend environment variable blueprint
│   ├── .env                         # Local backend environment file
│   ├── requirements.txt             # Python dependencies (FastAPI, SQLAlchemy, google-genai, etc.)
│   ├── seed_data.py                 # Standalone script to populate sample test leads
│   └── app/
│       ├── main.py                  # FastAPI application entry point, CORS, startup lifecycle
│       ├── core/
│       │   ├── config.py            # Pydantic Settings & environment variable loader
│       │   └── gemini.py            # Google Gemini API client initializer (safe fallback if key unset)
│       ├── db/
│       │   ├── base.py              # SQLAlchemy Declarative Base
│       │   ├── session.py           # SQLite connection engine & get_db session dependency
│       │   └── init_db.py           # Automatic schema creation on server startup
│       ├── models/
│       │   └── lead.py              # Full SQLAlchemy Lead model with complete pipeline lifecycle fields
│       ├── schemas/
│       │   └── lead.py              # Pydantic validation schemas (Create, Update, Out, Stats, Pagination)
│       ├── crud/
│       │   └── crud_lead.py         # Database query operations, filters, stats, and seeder
│       ├── api/v1/
│       │   ├── api.py               # Central v1 APIRouter
│       │   └── endpoints/
│       │       ├── leads.py         # CRUD, search, stats, and seed endpoints
│       │       └── health.py        # System health & Gemini config diagnostic endpoint
│       └── services/
│           └── README.md            # Architecture blueprint for Stages 2-6 (Scoring, Audit, Gemini, Demos)
│
└── frontend/                        # Next.js 14 + Tailwind CSS Frontend
    ├── package.json                 # Node.js dependencies (Next.js, React, Tailwind, Lucide Icons)
    ├── tsconfig.json                # TypeScript configuration
    ├── tailwind.config.js           # Sleek agency color tokens, dark mode & animations
    ├── postcss.config.js            # PostCSS configuration
    ├── next.config.js               # Next.js configuration & API proxies
    ├── .env.example                 # Frontend environment template
    ├── .env.local                   # Local frontend environment (NEXT_PUBLIC_API_URL)
    └── src/
        ├── types/
        │   └── lead.ts              # TypeScript type definitions matching backend schemas
        ├── lib/
        │   └── api.ts               # Type-safe API client for FastAPI endpoints
        ├── app/
        │   ├── globals.css          # Tailwind directives, glassmorphic card classes, scrollbars
        │   ├── layout.tsx           # Global HTML layout with Google Inter typography
        │   └── page.tsx             # Interactive Agency Dashboard page
        └── components/
            ├── Header.tsx           # Top nav with backend status indicator and 1-click seeding
            ├── StatsOverview.tsx    # 5 Key pipeline metric cards (Needs Website, Demos, Score, etc.)
            ├── FilterBar.tsx        # Search bar, pipeline status tabs, and website filter
            ├── LeadTable.tsx        # High-density leads table with badges and contact shortcuts
            ├── LeadDetailModal.tsx  # Detailed slide-over viewing all stages and copyable drafts
            ├── CreateLeadModal.tsx  # Form to manually add target businesses
            └── EditLeadModal.tsx    # Form to modify existing leads and pipeline stages
```

---

## ⚙️ Prerequisites

- **Python 3.10+** (Python 3.12 recommended)
- **Node.js 18+** & **npm** (Node.js 20+ LTS recommended)
- **Google Gemini API Key** (Get free key from [Google AI Studio](https://aistudio.google.com/))

---

## 🚀 Step-by-Step Installation & Setup

### 1. Configure Environment Variables

1. Copy `.env.example` to `backend/.env`:
   ```bash
   # From project root:
   cp .env.example backend/.env
   ```
2. Open `backend/.env` and add your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   DATABASE_URL=sqlite:///./agency_leads.db
   BACKEND_HOST=0.0.0.0
   BACKEND_PORT=8000
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```
   > ⚠️ **Security Reminder**: Never commit `.env` to Git. The `.gitignore` file is pre-configured to ignore all `.env` files.

---

### 2. Backend Setup & Run (FastAPI)

1. Open a terminal in the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. *(Optional)* Seed initial test leads:
   ```bash
   python seed_data.py
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - **API Server**: [http://localhost:8000](http://localhost:8000)
   - **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Alternative ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
   - **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### 3. Frontend Setup & Run (Next.js)

1. Open a separate terminal in the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Verify or create `frontend/.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Start the Next.js development server:
   ```bash
   npm run dev
   ```
5. Open your browser and navigate to:
   - **Dashboard**: [http://localhost:3000](http://localhost:3000)

---

## 🗄️ Database & Lead Model Design

The SQLite database (`backend/agency_leads.db`) is automatically initialized upon running FastAPI.

The `Lead` model contains all fields necessary to support the entire end-to-end pipeline:

| Field | Type | Description |
|---|---|---|
| `id` | Integer (PK) | Unique lead identifier |
| `business_name` | String(255) | Name of the target prospect |
| `industry` | String(100) | Business niche (Dental, Roofing, Cafe, etc.) |
| `location` | String(255) | City, State or geographic area |
| `website_url` | String(500) | Existing website URL (nullable) |
| `has_website` | Boolean | **False** flags prime opportunities for new websites |
| `email` | String(255) | Contact email address |
| `phone` | String(100) | Contact phone number |
| `instagram_handle` | String(100) | Instagram handle (e.g. `@artisanbakery_atx`) |
| `source` | String(50) | `manual`, `google_maps`, `instagram`, `csv`, `n8n` |
| `status` | String(50) | `new`, `analyzed`, `scored`, `outreach_generated`, `demo_generated`, `contacted`, `converted`, `rejected` |
| `lead_score` | Integer (0-100) | AI opportunity score |
| `score_reasons` | Text | Explanatory breakdown for the score |
| `website_analysis` | Text | Technical & UX audit report |
| `outreach_email_subject`| String(255) | AI generated cold email subject |
| `outreach_email_body` | Text | Personalized cold email pitch |
| `outreach_instagram_dm` | Text | Personalized Instagram direct message |
| `demo_url` | String(500) | Hosted preview link of AI-generated demo |
| `demo_preview_html` | Text | Raw HTML prototype of generated site |
| `notes` | Text | Agency internal notes |
| `created_at` / `updated_at` | DateTime | Automatic timestamps |

---

## 🔌 API Endpoints (v1)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Diagnostic status (DB connection, Gemini API key presence) |
| `GET` | `/api/v1/leads` | List leads (supports `search`, `status`, `has_website`, `min_score`, `page`, `page_size`) |
| `GET` | `/api/v1/leads/stats` | Aggregated dashboard metrics & status breakdown |
| `POST` | `/api/v1/leads` | Create a new lead |
| `POST` | `/api/v1/leads/seed` | Seed realistic demo leads for 1-click testing |
| `GET` | `/api/v1/leads/{id}` | Retrieve complete lead details |
| `PUT` | `/api/v1/leads/{id}` | Update lead fields or advance pipeline status |
| `DELETE` | `/api/v1/leads/{id}` | Permanently delete a lead |

---

## 🔮 What Remains to be Implemented

As planned for the incremental rollout, the remaining components to build in future stages are:

1. **Stage 2: Lead Scoring Service (`backend/app/services/lead_scorer.py`)**
   - Heuristics + Gemini prompt to compute opportunity score based on revenue potential and online gaps.
2. **Stage 3: Website Analyzer (`backend/app/services/website_analyzer.py`)**
   - Web scraping with `httpx` & `BeautifulSoup4`.
   - SSL check, mobile responsiveness analysis, and UX critique.
3. **Stage 4: AI Outreach Generator (`backend/app/services/outreach_generator.py`)**
   - Google Gemini 2.5 Flash pipeline generating custom cold emails and Instagram DMs citing audit findings.
4. **Stage 5: AI Website Demo Generator (`backend/app/services/demo_builder.py`)**
   - Code generation engine creating modern Tailwind/HTML landing page prototypes tailored to each lead.
5. **Stage 6: Demo Deployment (`backend/app/services/deployment.py`)**
   - Instant deployment of generated demos to static hosting (e.g. Vercel, Netlify, or subdomains).
6. **Stage 8: n8n Automation Workflows**
   - Webhook integration to ingest leads from Google Maps or Instagram scrapers automatically.
