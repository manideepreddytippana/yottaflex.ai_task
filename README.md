# Marketing Campaign Attribution & ROI Analysis System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178c6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646cff.svg)](https://vitejs.dev/)
[![Tests Passing](https://img.shields.io/badge/tests-41%2F41%20passing-brightgreen.svg)]()
[![Seed: 20261022](https://img.shields.io/badge/seed-20261022-purple.svg)]()

A reproducible, auditable end-to-end data engineering and analytics system that generates realistic synthetic marketing data, stores it in a relational schema, reconstructs multi-channel customer journeys, applies multi-touch attribution models, performs cent-perfect financial reconciliation, detects known data-quality anomalies, and exposes results through a FastAPI backend and a responsive React/TypeScript analytics dashboard.

---

## 1. System Overview & Core Capabilities

- **Deterministic Generator**: Parameterized generator driven by fixed random seed `20261022`, producing identical output bytes across runs for both `starter` and `full` scales (500 campaigns, 50,000 contacts, 200,000 touchpoints, 10,000 opportunities).
- **PostgreSQL & SQLAlchemy Relational Schema**: 12 core normalized entities, 2 campaign bridge tables, 2 append-only lifecycle event tables, and audit log tables with primary and foreign key constraints.
- **6-Point Touchpoint Eligibility Filter**: Enforces chronological conversion order, 180-day lookback window, supported identity linkage, campaign activity intervals, active channel validation, and synthetic consistency.
- **Multi-Touch Attribution Engine**: Implements First-Touch, Last-Touch, and Linear multi-touch attribution models with deterministic remainder cent distribution (shares sum to exactly `1.0` and revenue sums to the exact eligible cent).
- **Financial Reconciliation & Deduplication**: Base currency normalization (INR), duplicate transaction deduplication by `economic_transaction_key`, and campaign ROI computation with explicit coverage status tracking (`COMPLETE`, `INCOMPLETE_COST`, `CURRENCY_UNRESOLVED`, `ZERO_COST`).
- **Zero-Leakage Exception Detector**: Detects 5 controlled anomaly scenarios directly from source records with 100% Precision, 100% Recall, and 1.00 F1 score without accessing the isolated ground-truth file.
- **Multi-Format Deliverables & Reproducibility Suite**: Generates normalized CSVs, portable PostgreSQL `seed.sql`, `manifest.json`, `checksums.sha256`, and verification harness comparing SHA-256 hashes between independent runs.
- **REST API & Modern Analytics Dashboard**: FastAPI backend exposing 17 endpoints and an integrated 5-page React dashboard (Overview, Attribution Comparison, Customer Journey, Exceptions & Data Quality, Runs & Reproducibility).

---

## 2. Architecture & Design Principles

```text
Versioned Configuration (config/starter.yaml, config/full.yaml; Seed: 20261022)
                                 │
                                 ▼
                     Deterministic Synthetic Generator
       Master Data ──> Contacts ──> Touchpoints ──> Web Sessions
            │                │             │              │
            ▼                ▼             ▼              ▼
       Campaigns           Leads ──> Opportunities ──> Orders & Events
                                 │
                                 ▼
                  Relational Relational Database (PostgreSQL / SQLite)
                                 │
                                 ▼
                    Automated Quality Validation (39 Checks)
                                 │
                                 ▼
                   Customer Journey Reconstruction Engine
             (6-Point Touchpoint Eligibility & 180-Day Lookback)
                                 │
                                 ▼
                     Attribution Calculation Engine
             (First-Touch, Last-Touch, Linear Multi-Touch)
                                 │
                                 ▼
                   Financial Reconciliation & Campaign ROI
             (FX Normalization, Economic Deduplication, INR Base)
                                 │
                                 ▼
             Zero-Leakage Exception Detector ──> Isolated Ground Truth
                                 │
                                 ▼
              Multi-Format Exports (CSV, seed.sql, manifest, sha256)
                                 │
                                 ▼
                  FastAPI REST API Backend (Port 8000)
                                 │
                                 ▼
             React + TypeScript + Vite Analytics Dashboard (Port 5173)
```

### Deterministic Identifier Contracts
| Entity | Prefix Pattern | Example |
| :--- | :--- | :--- |
| Campaign | `CMP-YYYY-{counter:06d}` | `CMP-2026-000001` |
| Channel | `CHN-{counter:03d}` | `CHN-001` |
| Creative | `CRT-{counter:03d}` | `CRT-001` |
| Audience | `AUD-{counter:03d}` | `AUD-001` |
| Contact | `CON-{counter:06d}` | `CON-000001` |
| Touchpoint | `TOUCH-CON-{id}-{counter:06d}` | `TOUCH-CON-000001-000001` |
| Web Session | `SES-YYYY-{counter:06d}` | `SES-2026-000001` |
| Lead | `LED-YYYY-{counter:06d}` | `LED-2026-000001` |
| Opportunity | `OPP-YYYY-{counter:06d}` | `OPP-2026-000001` |
| Order | `ORD-YYYY-{counter:06d}` | `ORD-2026-000001` |
| Cost Record | `COST-YYYY-{counter:06d}` | `COST-2026-000001` |
| Data Issue | `ISSUE-{counter:06d}` | `ISSUE-000001` |
| Ground Truth | `GT-SCENARIO-{num}` | `GT-SCENARIO-1` |

---

## 3. Repository Structure

The project is organized into two primary folders separating backend engineering and frontend visualization:

```text
Yotaflex_task/
├── README.md                          # Project documentation and CLI guide
├── implementation_plan.md             # Detailed engineering specification
│
├── backend/                           # Complete Python data engineering, database, & API backend
│   ├── requirements.txt               # Project Python dependencies
│   ├── pytest.ini                     # Pytest configuration and pythonpath
│   ├── .env.example                   # Environment configuration template
│   ├── config/                        # Dataset configurations (starter.yaml, full.yaml)
│   ├── docs/                          # Architecture, data dictionary, schema, and rule specs
│   ├── sql/                           # Canonical PostgreSQL DDL script (schema.sql)
│   ├── src/                           # Core implementation modules
│   │   └── attribution/
│   │       ├── config.py              # Configuration loader and SHA-256 hash
│   │       ├── ids.py                 # Deterministic monotonic ID generator & regex validator
│   │       ├── generator/             # Deterministic synthetic generators
│   │       ├── db/                    # SQLAlchemy 2.0 ORM models & session management
│   │       ├── pipeline/              # Validation (39 checks), journeys, attribution, exceptions
│   │       ├── services/              # Domain-specific business logic & data access services
│   │       │   ├── health.py          # Database connectivity & health status
│   │       │   ├── runs.py            # Provenance & automated validation inspection
│   │       │   ├── campaigns.py       # Performance, budget, and multi-model ROI
│   │       │   ├── attribution.py     # Multi-touch attribution comparison & order tracing
│   │       │   ├── contacts.py        # Customer journey timeline reconstruction
│   │       │   ├── issues.py          # Exception detection & data quality issues
│   │       │   ├── metrics.py         # Precision, recall, and F1 evaluation metrics
│   │       │   └── exports.py         # Manifests & SHA-256 deliverable listings
│   │       ├── export/                # CSV, SQL seed, JSON manifest, and SHA-256 checksums
│   │       └── api/                   # FastAPI REST backend and static dashboard mounts
│   ├── scripts/                       # Command-line entrypoints
│   │   ├── run_pipeline.py            # End-to-end pipeline runner
│   │   ├── generate_data.py           # Synthetic dataset generator
│   │   ├── load_data.py               # Ingests generated CSVs into database
│   │   ├── validate_data.py           # Executes 39 validation checks
│   │   └── verify_reproducibility.py  # Bit-for-bit repeatability verification
│   ├── data/                          # Generated datasets, isolated ground truth, & SQLite DB
│   └── tests/                         # Complete test suite (41 tests across unit, integration, repro)
│
└── frontend/                          # React 18 + TypeScript + Vite Analytics Dashboard
    ├── package.json                   # Frontend dependencies
    ├── vite.config.ts                 # Vite bundler (builds into backend/src/attribution/api/static)
    ├── tsconfig.json                  # TypeScript compiler options
    ├── index.html                     # HTML root
    └── src/                           # React application
        ├── App.tsx                    # Shell layout and navigation tabs
        ├── index.css                  # Modern high-density dark UI design system
        ├── types.ts                   # TypeScript data contracts
        ├── api.ts                     # REST API client
        ├── components/                # MetricCard, SvgBarChart, Badge, StatusIndicator
        └── pages/                     # 5 analytics screens (Overview, Attribution, Journey, etc.)
```

---

## 4. Quick Start & Installation

### Prerequisites
- Python 3.11+
- Node.js v18+ and npm (for frontend development)

### 1. Set Up Python Backend Environment
```bash
# Navigate to the backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate       # On Windows
source venv/bin/activate       # On Linux/macOS

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

### 2. Run the Full Test Suite
```bash
# From within the backend directory:
python -m pytest tests/
```
*Expected: 41 passed across unit, integration, reproducibility, and API suites.*

---

## 5. Command-Line Interface (CLI) Reference

Run all CLI commands from the `backend/` directory:

### Generate Synthetic Dataset
```bash
cd backend

# Generate starter dataset (25 campaigns, 1,000 contacts, 4,000 touchpoints)
python scripts/generate_data.py --config config/starter.yaml --output data/generated/starter

# Generate full-scale dataset (500 campaigns, 50,000 contacts, 200,000 touchpoints, 10,000 opportunities)
python scripts/generate_data.py --config config/full.yaml --output data/generated/full
```

### Load Dataset into Database
```bash
cd backend

# Loads all normalized CSV tables into PostgreSQL or SQLite
python scripts/load_data.py --input data/generated/starter --clean
```

### Run Validation Checks
```bash
cd backend

# Executes all 39 structural, temporal, financial, and lifecycle validation rules
python scripts/validate_data.py --input data/generated/starter
```

### Execute End-to-End Pipeline
```bash
cd backend

# Runs generation, validation, attribution, financial reconciliation, and exception detection
python scripts/run_pipeline.py --config config/starter.yaml --output data/generated/starter
```

### Verify Bit-for-Bit Reproducibility
```bash
cd backend

# Generates two independent runs with seed 20261022 into separate directories and verifies SHA-256 hashes
python scripts/verify_reproducibility.py --config config/starter.yaml
```

---

## 6. REST API Reference

The FastAPI backend provides typed endpoints documented interactively via OpenAPI / Swagger UI.

### Start Backend Server
```bash
cd backend
python -m uvicorn src.attribution.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Interactive Analytics Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Interactive Analytics Dashboard**: [http://localhost:8000/](http://localhost:8000/)

### Primary Endpoints Catalog
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | API health status and database connectivity |
| `GET` | `/api/runs` | List execution runs and scale metadata |
| `GET` | `/api/runs/{run_id}` | Detailed run provenance, row counts, and checksums |
| `GET` | `/api/runs/{run_id}/validation` | 39 automated check results and overall status |
| `GET` | `/api/campaigns` | Paginated campaigns with spend, linear revenue, and ROI |
| `GET` | `/api/campaigns/{id}` | Detailed campaign breakdown with creatives and audiences |
| `GET` | `/api/campaigns/{id}/roi` | Multi-model ROI breakdown (First, Last, Linear) |
| `GET` | `/api/attribution/compare` | Compares models and validates 100% financial reconciliation |
| `GET` | `/api/orders/{id}/attribution` | Order attribution breakdown with contributing touchpoint weights |
| `GET` | `/api/contacts/{id}/journey` | Chronological journey stream with post-conversion exclusion tags |
| `GET` | `/api/issues` | Filterable data quality exception log |
| `GET` | `/api/issues/{id}` | Detailed exception context and affected entity links |
| `GET` | `/api/metrics` | Evaluation metrics against ground truth (Precision, Recall, F1) |
| `GET` | `/api/exports/{run_id}` | List exported files with SHA-256 checksums |

---

## 7. Analytics Dashboard Frontend

The analytics dashboard is built with **React 18**, **TypeScript**, and **Vite**, featuring a high-density, accessible dark-theme UI.

### Start Frontend Dev Server
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173/](http://localhost:5173/) in your browser.

### Build Frontend for Production
```bash
cd frontend
npm run build
```
*Compiles directly to `backend/src/attribution/api/static`, allowing the FastAPI server to serve the complete dashboard at `http://localhost:8000/` without needing Node.js in production.*

### The 5 Dashboard Pages
1. **Overview**: Executive KPI cards (Campaigns, Spend, Attributed Revenue, ROI, Validation status), reporting currency indicator, and spend coverage warnings.
2. **Attribution Comparison**: Interactive model comparison (First-Touch vs Last-Touch vs Linear), revenue allocation SVG grouped bar chart, model ranking matrix, and method disclaimer.
3. **Customer Journey Explorer**: Customer timeline tracer searching by Contact ID (e.g., `CON-000262`, `CON-000001`), visualizing touchpoints, web sessions, leads, opportunities, orders, and highlighting post-conversion touches excluded by rule.
4. **Exceptions & Data Quality**: Evaluation scorecard (100% Precision, 100% Recall, 1.00 F1 score) and filterable audit log of data quality anomalies with mitigation decisions.
5. **Runs & Reproducibility**: Run provenance scorecard, 18-entity row count matrix, and SHA-256 checksum audit table with direct download references.

---

## 8. Controlled Anomaly Scenarios & Evaluation

The system injects 5 controlled anomaly scenarios to test pipeline robustness, with labels strictly preserved in `data/ground_truth/ground_truth.csv` outside the detector's input path:

| Scenario | Injected Condition | Automated Mitigation Decision | Detector Action |
| :--- | :--- | :--- | :--- |
| **1. DUPLICATE_REVENUE** | Two completed orders share identical `economic_transaction_key` | `COUNT_ONCE_FLAG_DUPLICATE` | Revenue attributed once; second order attributed 0.00 INR and logged to `data_issue` |
| **2. POST_CONVERSION_TOUCH** | Marketing touchpoint timestamp occurs after conversion order date | `EXCLUDE_FROM_ATTRIBUTION` | Touch excluded from attribution universe; conversion assigned to preceding eligible touches |
| **3. CURRENCY_MISMATCH** | Cost record in foreign currency (`EUR`) lacks valid exchange rate | `BLOCK_ROI_FLAG_UNRESOLVED_FX` | Spend marked incomplete; campaign ROI marked provisional/unavailable |
| **4. MISSING_CAMPAIGN_COST** | Active marketing campaign has zero recorded cost records | `MARK_INCOMPLETE_COST_ROI_UNAVAILABLE` | Campaign spend coverage marked `INCOMPLETE`; ROI marked unavailable |
| **5. UNSUPPORTED_IDENTITY_LINK** | Anonymous session with `NONE` evidence artificially linked to contact | `QUARANTINE_IDENTITY_LINK` | Touch isolated from journey; visible in exception log |

### Evaluation Metrics Against Ground Truth
- **Precision**: `100.00%` (0 False Positives)
- **Recall**: `100.00%` (0 False Negatives across all 5 categories)
- **F1 Score**: `1.00`
- **Reconciliation Pass Rate**: `100.00%` (Difference: `0.00 INR` on both Starter and Full scales)


