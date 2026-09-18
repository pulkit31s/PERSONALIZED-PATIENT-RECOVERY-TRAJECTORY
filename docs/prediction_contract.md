# Prediction Contract

> **WARNING:** The data and logic described in this system are for **development and mock data only**. All data is synthetic. This is **NOT** a clinical tool and does **NOT** use real MIMIC-IV data.

## API Contract Overview
The API provides a standardized interface for requesting patient trajectory predictions at a specific point in time during an ICU stay.

## PredictionRequest Schema
| Field | Type | Required | Description |
|---|---|---|---|
| `stay_id` | `str` | Yes | The unique identifier for the ICU stay (e.g., 'mock_stay_001'). |
| `prediction_time` | `datetime` | Yes | The exact time `t` to generate predictions for. Must be UTC timezone-aware. |
| `include_explanations` | `bool` | No | Default `False`. Whether to include feature importance/explanations. |

## PredictionResponse Schema
The response contains an array of `EndpointPrediction` models within a `PredictionResponse` model.

### PredictionResponse
| Field | Type | Description |
|---|---|---|
| `stay_id` | `str` | The stay identifier requested. |
| `prediction_time` | `datetime` | The prediction time requested. |
| `predictions` | `list[EndpointPrediction]` | A list of predictions for each endpoint. |
| `version` | `str` | The version of the API/models used. |

### EndpointPrediction
| Field | Type | Description |
|---|---|---|
| `endpoint_name` | `str` | The name of the endpoint (e.g., 'organ_support_initiation_24h'). |
| `prediction_type` | `str` | 'binary', 'regression', or 'survival'. |
| `value` | `float` | The predicted value (probability, hours, or SOFA score change). |
| `is_censored` | `bool` | True if the prediction cannot be made due to censoring (e.g., already on support). |
| `explanations` | `dict` | (Optional) Feature attributions if requested. |

## Error Responses
| HTTP Status | Meaning | Reason |
|---|---|---|
| `404 Not Found` | Stay not found | The `stay_id` does not exist in the history repository. |
| `422 Unprocessable Entity` | Invalid request | Missing fields, invalid types, or non-timezone-aware `prediction_time`. |
| `500 Internal Server Error` | Pipeline failure | Unexpected error during feature building or prediction. |
| `503 Service Unavailable` | Artifact failure | The model manifest or artifacts could not be loaded. |

## Versioning Policy
- **API Version**: Specified in the URL path (e.g., `/api/v1/predict`).
- **Model Version**: Included in the `PredictionResponse.version` field and managed via `artifacts/mock/selected_models_v1.json`.

## Example Request/Response

**Request:**
```json
{
  "stay_id": "mock_stay_001",
  "prediction_time": "2026-01-01T18:00:00Z",
  "include_explanations": false
}
```

**Response:**
```json
{
  "stay_id": "mock_stay_001",
  "prediction_time": "2026-01-01T18:00:00Z",
  "predictions": [
    {
      "endpoint_name": "organ_support_initiation_24h",
      "prediction_type": "binary",
      "value": 0.15,
      "is_censored": false
    }
  ],
  "version": "1.0.0"
}
```

## Mock Data Status
Currently, all predictions are deterministically generated based on feature hashing using mock data. No real inference is taking place.

## Integration Notes for Dashboard Team (Vedant)
- The dashboard should gracefully handle `is_censored = true` by displaying a "N/A" or "Already on support" state rather than a raw probability.
- Timezones will always be UTC. Convert to local time on the client side if necessary.
- Explanation payloads will be key-value pairs of feature names and attribution scores (pending real SHAP implementation).
