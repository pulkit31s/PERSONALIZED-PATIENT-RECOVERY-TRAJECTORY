import pytest
from datetime import datetime, timezone, timedelta
from src.serving.prediction_pipeline import PredictionPipeline
from src.serving.validation import StayNotFoundError, InvalidPredictionTimeError
from src.mock.mock_data import BASE_TIME

@pytest.fixture
def pipeline():
    return PredictionPipeline()

def test_basic_prediction(pipeline):
    t = BASE_TIME + timedelta(hours=6)
    resp = pipeline.predict('mock_stay_001', t)
    assert resp.schema_version == 'prediction_schema_v1'
    assert resp.request.stay_id == 'mock_stay_001'
    assert resp.predictions.sofa_delta_24h.unit == 'SOFA points'
    assert resp.replay.future_data_used is False

def test_deterministic(pipeline):
    t = BASE_TIME + timedelta(hours=6)
    r1 = pipeline.predict('mock_stay_001', t)
    r2 = pipeline.predict('mock_stay_001', t)
    assert r1.predictions.sofa_delta_24h.value == r2.predictions.sofa_delta_24h.value
    assert r1.predictions.organ_support_initiation.probability == r2.predictions.organ_support_initiation.probability

def test_unknown_stay(pipeline):
    with pytest.raises(StayNotFoundError):
        pipeline.predict('nonexistent_stay', BASE_TIME)

def test_prediction_before_admission(pipeline):
    with pytest.raises(InvalidPredictionTimeError):
        pipeline.predict('mock_stay_001', BASE_TIME - timedelta(hours=1))

def test_prediction_after_discharge(pipeline):
    with pytest.raises(InvalidPredictionTimeError):
        pipeline.predict('mock_stay_001', BASE_TIME + timedelta(hours=100))  # outtime is +72h

def test_metadata_present(pipeline):
    t = BASE_TIME + timedelta(hours=6)
    resp = pipeline.predict('mock_stay_001', t)
    assert resp.metadata.pipeline_version == 'pipeline_v1'
    assert resp.metadata.model_manifest_version == 'selected_models_v1'
    assert resp.data_quality.is_mock_data is True

def test_explanations_included(pipeline):
    t = BASE_TIME + timedelta(hours=6)
    resp = pipeline.predict('mock_stay_001', t, include_explanations=True)
    assert resp.explanations is not None
    assert resp.explanations.status == 'mock'

def test_explanations_excluded(pipeline):
    t = BASE_TIME + timedelta(hours=6)
    resp = pipeline.predict('mock_stay_001', t, include_explanations=False)
    assert resp.explanations is None

def test_history_truncated_at(pipeline):
    t = BASE_TIME + timedelta(hours=6)
    resp = pipeline.predict('mock_stay_001', t)
    assert resp.replay.history_truncated_at == t
