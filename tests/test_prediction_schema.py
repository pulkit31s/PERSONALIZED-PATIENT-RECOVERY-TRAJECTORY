import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from src.schemas.prediction import PredictionRequest, PredictionResponse

def test_valid_request():
    req = PredictionRequest(
        stay_id='mock_stay_001',
        prediction_time=datetime(2026, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
    )
    assert req.stay_id == 'mock_stay_001'

def test_missing_stay_id():
    with pytest.raises(ValidationError):
        PredictionRequest(
            prediction_time=datetime(2026, 1, 1, 18, 0, 0, tzinfo=timezone.utc)
        )

def test_empty_stay_id():
    with pytest.raises(ValidationError):
        PredictionRequest(
            stay_id='',
            prediction_time=datetime(2026, 1, 1, 18, 0, 0, tzinfo=timezone.utc)
        )

def test_naive_timestamp_rejected():
    with pytest.raises(ValidationError):
        PredictionRequest(
            stay_id='mock_stay_001',
            prediction_time=datetime(2026, 1, 1, 18, 0, 0)  # naive!
        )

def test_include_explanations_default():
    req = PredictionRequest(
        stay_id='test',
        prediction_time=datetime(2026, 1, 1, 18, 0, 0, tzinfo=timezone.utc)
    )
    assert req.include_explanations is True

def test_request_json_roundtrip():
    req = PredictionRequest(
        stay_id='test',
        prediction_time=datetime(2026, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
        include_explanations=False
    )
    data = req.model_dump_json()
    req2 = PredictionRequest.model_validate_json(data)
    assert req2.stay_id == req.stay_id
