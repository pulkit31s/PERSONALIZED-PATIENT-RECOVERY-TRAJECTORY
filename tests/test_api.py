import pytest
from fastapi.testclient import TestClient
from api.main import app
from src.mock.mock_data import BASE_TIME
from datetime import timedelta

@pytest.fixture
def client():
    # Make sure app startup event is triggered manually if needed, TestClient handles lifespan
    with TestClient(app) as c:
        yield c

def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'ok'
    assert data['mock_mode'] is True

def test_model_metadata(client):
    resp = client.get('/model-metadata')
    assert resp.status_code == 200
    data = resp.json()
    assert 'manifest_version' in data or 'tasks' in data

def test_predict_valid(client):
    body = {
        'stay_id': 'mock_stay_001',
        'prediction_time': (BASE_TIME + timedelta(hours=6)).isoformat(),
        'include_explanations': True
    }
    resp = client.post('/predict', json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data['schema_version'] == 'prediction_schema_v1'
    assert 'predictions' in data
    assert 'padding_indicators' in data['data_quality']

def test_predict_unknown_stay(client):
    body = {
        'stay_id': 'nonexistent',
        'prediction_time': (BASE_TIME + timedelta(hours=6)).isoformat(),
    }
    resp = client.post('/predict', json=body)
    assert resp.status_code == 404
    assert resp.json()['error'] == 'stay_not_found'

def test_predict_invalid_schema(client):
    body = {'prediction_time': 'not-a-datetime'}
    resp = client.post('/predict', json=body)
    assert resp.status_code == 422

def test_predict_missing_stay_id(client):
    body = {
        'prediction_time': (BASE_TIME + timedelta(hours=6)).isoformat(),
    }
    resp = client.post('/predict', json=body)
    assert resp.status_code == 422

def test_api_and_pipeline_match(client):
    from src.serving.prediction_pipeline import PredictionPipeline
    t = BASE_TIME + timedelta(hours=6)
    pipe = PredictionPipeline()
    pipe_resp = pipe.predict('mock_stay_001', t)

    body = {
        'stay_id': 'mock_stay_001',
        'prediction_time': t.isoformat(),
        'include_explanations': True
    }
    api_resp = client.post('/predict', json=body)
    api_data = api_resp.json()
    assert api_data['predictions']['recovery']['delta_24h'] == pipe_resp.predictions.recovery.delta_24h
    assert api_data['predictions']['organ_support']['calibrated_probability'] == pipe_resp.predictions.organ_support.calibrated_probability
