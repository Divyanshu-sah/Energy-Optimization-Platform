# EnergiX Copilot Backend

FastAPI backend for the Industrial Energy Optimization Platform.

## Setup

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Run the server:**
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Or run directly:
```bash
python app.py
```

## API Endpoints

### Machines
- `GET /api/machines` - List all machines
- `GET /api/machines/{machine_id}` - Get machine details

### ML Inference
- `POST /api/analyze` - Anomaly detection
- `POST /api/classify-efficiency` - Efficiency classification
- `POST /api/forecast` - Demand forecasting

### Data
- `GET /api/alerts` - List alerts
- `GET /api/recommendations` - List recommendations
- `GET /api/dashboard-summary` - Dashboard KPIs
- `GET /api/plants` - List plants

### Simulation
- `POST /api/simulate` - Run scenario simulation

## Frontend Integration

The frontend will automatically use the API when available. Set the environment variable in `frontend/EnergiX_Copilot/.env`:
```
VITE_API_URL=http://localhost:8000
```

With Vite proxy configured, you can just use relative paths (`/api/...`).
