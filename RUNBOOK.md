# RUNBOOK

## Prerequisites

- Python >= 3.10
- pip

## Setup

```bash
git clone <repo-url>
cd healthcare-da
pip install -r requirements.txt
```

## Running

### Tests
```bash
pytest tests/ -v --tb=short
```

### API Server (Development)
```bash
uvicorn api.main:app --reload --port 8000
```

### API Server (Production-like)
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Dashboard Launch (Phase 9)
```bash
streamlit run dashboard/app.py
```
This runs the Retrospective Sequential Replay dashboard on http://localhost:8501.

## Modes

### Mock Mode vs Real Artifact Mode
- Currently, the system runs in Mock Mode, generating synthetic predictions deterministically.
- `selected_models_v1.json` describes "mock" models.
- Replace mock artifacts in `artifacts/mock/` with real ones (and set the corresponding family to xgboost/gru) when real models are available.

## Known Limitations

- All clinical data is mock synthetic data.
- No real MIMIC data extraction logic is implemented in this repository.
- Predictions use a mock deterministic random generator.
- Artifact loader checks configurations but mock artifacts don't load physical weights.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/model-metadata` | GET | Model manifest info |
| `/predict` | POST | Generate predictions |

## Error Codes

| Code | Meaning |
|------|--------|
| 404 | Stay not found |
| 422 | Invalid request/timestamp |
| 503 | Artifact loading failure / Artifact Mismatch |
| 500 | Internal server error |

## Example API Call

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"stay_id": "mock_stay_001", "prediction_time": "2026-01-01T18:00:00Z"}'
```

## Troubleshooting

- If tests fail with import errors, ensure you run `pytest` from the project root.
- If API returns 503, ensure `artifacts/mock/selected_models_v1.json` exists and versions match the `feature_schema_v1.yaml`.
- All timestamps must be timezone-aware (include `Z` or `+00:00`).
