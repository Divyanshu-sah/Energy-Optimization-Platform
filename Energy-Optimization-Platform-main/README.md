# EnergiX Copilot

> **Where every kilowatt counts.** An AI-powered smart system that monitors, predicts, and optimizes industrial energy consumption in real-time — built for Industry 4.0.

---

## Theme: Industry 4.0

Industries waste up to **30%** of energy through idle machines, inefficient operations, and unpredictable demand spikes. EnergiX Copilot tackles this head-on with a **smart monitoring & optimization system** powered by machine learning.

---

## What It Does

- **Anomaly Detection** — Identifies abnormal energy consumption patterns across machines in real-time
- **Efficiency Classification** — Rates machine performance and pinpoints energy waste
- **Demand Forecasting** — Predicts future energy demand to enable proactive load balancing
- **Smart Recommendations** — Generates actionable insights to cut energy costs
- **Live Dashboard** — Visualizes plant-wide energy health with interactive charts and KPIs

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Frontend   │────▶│  FastAPI     │────▶│  ML Models  │
│  React +    │◀────│  Backend     │◀────│  Isolation  │
│  Tailwind   │     │              │     │  Forest +   │
│  Recharts   │     │              │     │  XGBoost    │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Vite, Tailwind CSS, Recharts, Framer Motion |
| Backend | FastAPI, Uvicorn |
| ML | XGBoost, Isolation Forest, Scikit-learn |
| Data | Pandas, NumPy, Synthetic industrial datasets |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- PostgreSQL 14+ (optional — system falls back to CSV files if unavailable)

### 1. Database Setup (Optional but Recommended)

```bash
# Ensure PostgreSQL is running, then build the database
python database/build_db.py
```

Default credentials: `postgres / energix123` on `localhost:5432`

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Start the API server
uvicorn backend.app:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The app will be available at **http://localhost:3000**

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Frontend   │────▶│  FastAPI     │────▶│  ML Models  │
│  React +    │◀────│  Backend     │◀────│  Isolation  │
│  Tailwind   │     │              │     │  Forest +   │
│  Recharts   │     │              │     │  XGBoost    │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐
                    │  PostgreSQL  │
                    │  (optional,  │
                    │   falls back │
                    │   to CSV)    │
                    └──────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Vite, Tailwind CSS, Recharts, Framer Motion |
| Backend | FastAPI, Uvicorn |
| Database | PostgreSQL + SQLAlchemy ORM (optional) |
| ML | XGBoost, Isolation Forest, Scikit-learn |
| Data | Pandas, NumPy, Synthetic industrial datasets |

---

## Key Features

- **Real-time monitoring** of machine-level energy consumption
- **AI-driven alerts** for anomalies and inefficiencies
- **Predictive demand forecasting** for proactive planning
- **Scenario simulation** to test "what-if" conditions
- **Actionable recommendations** to reduce energy waste
- **PostgreSQL Integration** for persistent state (optional — falls back to CSV)
- **Loading states** across all pages for better UX

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/machines` | List all machines |
| GET | `/api/machines/{id}` | Get machine details |
| GET | `/api/alerts` | List alerts (filterable) |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge an alert |
| GET | `/api/recommendations` | List recommendations |
| POST | `/api/recommendations/{id}/apply` | Apply a recommendation |
| POST | `/api/recommendations/{id}/dismiss` | Dismiss a recommendation |
| GET | `/api/dashboard-summary` | Get dashboard overview |
| POST | `/api/analyze` | Run anomaly detection |
| POST | `/api/classify-efficiency` | Run efficiency classification |
| POST | `/api/forecast` | Run demand forecasting |

Full API docs available at **http://localhost:8000/docs** when server is running.

---

## 🏭 Built For

<div align="center">

### 🚀 GNA Hackathon 4.0  
**Industry 4.0 — Smart Manufacturing & Energy Optimization**

</div>

---

## 👥 Team Krantikaris

<div align="center">

| Team Members |
|--------------|
| 👨‍💻 Ayush (Data Guy + Simulator builder) |
| 👨‍💻 Dev Prakash Pandey (Data Guy + Simulator builder) |
| 👨‍💻 Divyanshu Kumar (Frontend designer) |
| 👨‍💻 Krishna Swarup (Frontend builder)|
| 👨‍💻 Manish Tiwari (Leader) |

</div>

---
