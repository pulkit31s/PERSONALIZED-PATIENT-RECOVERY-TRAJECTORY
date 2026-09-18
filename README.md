# Personalized Patient Recovery Trajectory

> **Status: Development / Mock Data Only**  
> All data is synthetic. This is NOT a clinical tool and does NOT use MIMIC-IV data.

## Overview

Retrospective ICU forecasting system with four research outputs:
1. SOFA change at +24 hours
2. SOFA change at +48 hours  
3. Remaining time until ICU stay ends
4. New organ-support initiation risk within 24 hours

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Tests

```bash
pytest tests/ -v
```

### Start the API

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Example Prediction Request

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "stay_id": "mock_stay_001",
    "prediction_time": "2026-01-01T18:00:00Z",
    "include_explanations": true
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

### Model Metadata

```bash
curl http://localhost:8000/model-metadata
```

## Project Structure

```
configs/              # Event dictionary, prediction schema
src/labels/           # Organ-support labeling logic
src/schemas/          # Pydantic request/response models
src/serving/          # Prediction pipeline, feature builder, history
src/mock/             # Mock data and predictors
api/                  # FastAPI application
tests/                # pytest test suite
data/demo/            # Synthetic CSV data
artifacts/mock/       # Mock model manifest and configs
docs/                 # Design documentation
```

## Mock Data

6 synthetic ICU stays with different scenarios:
- `mock_stay_001`: Normal 72h stay, no support
- `mock_stay_002`: Short 8h stay (censoring tests)
- `mock_stay_003`: Vasopressor starting 6h after admission
- `mock_stay_004`: Invasive ventilation starting 10h after admission
- `mock_stay_005`: Both supports from admission
- `mock_stay_006`: NIV only (non-qualifying)

## Key Design Decisions

1. **Temporal leakage prevention**: History is truncated at `event_time <= prediction_time`
2. **Half-open interval `(t, t+24h]`**: Events at t define state; events after t are the horizon
3. **Explicit censoring**: Incomplete follow-up is never silently treated as negative
4. **Deterministic mock predictions**: Based on feature hashing with fixed seeds
5. **Abstract interfaces**: FeatureBuilder, ArtifactLoader ready for real implementations

## What Is NOT Implemented

- Real MIMIC-IV data extraction
- Real model training (XGBoost, GRU)
- Calibration
- Final explainability (SHAP/LIME)
- Dashboard
- Production deployment
- Drug name normalization
- Route validation

## Integration Points

- **Sanskruti**: Feature engineering, model training
- **Vedant**: Dashboard, visualization
- Replace `MockFeatureBuilder` with real feature builder
- Replace `MockPredictor` with trained model inference
- Replace `MOCK_STAYS` with MIMIC-IV extraction

## License

Internal research project. Not for clinical use.
