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
| 503 | Artifact loading failure |
| 500 | Internal server error |

## Example API Call

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"stay_id": "mock_stay_001", "prediction_time": "2026-01-01T18:00:00Z"}'
```

## Troubleshooting

- If tests fail with import errors, ensure you run `pytest` from the project root
- If API returns 503, ensure `artifacts/mock/selected_models_v1.json` exists
- All timestamps must be timezone-aware (include `Z` or `+00:00`)
