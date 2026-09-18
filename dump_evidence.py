import json
from src.serving.prediction_pipeline import PredictionPipeline
from src.mock.mock_data import BASE_TIME
from datetime import timedelta

pipeline = PredictionPipeline()
t = BASE_TIME + timedelta(hours=6)
resp = pipeline.predict('mock_stay_001', t)

with open('docs/evidence/system/api_response.json', 'w') as f:
    f.write(resp.model_dump_json(indent=2))

manifest = pipeline.artifact_loader.load_model_manifest()
with open('docs/evidence/system/model_metadata.json', 'w') as f:
    json.dump(manifest, f, indent=2)
