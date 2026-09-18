from datetime import datetime
from typing import Optional, Dict, Any
from src.serving.history import load_stay_metadata, load_events, truncate_history_at
from src.serving.feature_builder import MockFeatureBuilder, FeatureBuilderInterface
from src.serving.artifacts import ArtifactLoader
from src.serving.validation import (
    validate_prediction_request, StayNotFoundError
)
from src.schemas.prediction import (
    PredictionResponse, RequestEcho, PredictionMetadata, ReplayInfo,
    Predictions, RecoveryPrediction, ICUStayTimePrediction, OrganSupportPrediction,
    DataQuality, TaskMetadata
)
from src.serving.postprocessing import postprocess_recovery, postprocess_icu_stay_time, postprocess_organ_support
from src.explainability.router import route_explanations
import logging
import hashlib
import numpy as np

class PredictionPipeline:
    """Pipeline for processing and generating predictions."""
    
    PIPELINE_VERSION = 'pipeline_v1'

    def __init__(self, artifacts_dir: Optional[str] = None, feature_builder: Optional[FeatureBuilderInterface] = None):
        self.artifact_loader = ArtifactLoader(artifacts_dir)
        self.feature_builder = feature_builder or MockFeatureBuilder()
        self.logger = logging.getLogger(__name__)

    def predict(self, stay_id: str, prediction_time: datetime, include_explanations: bool = True) -> PredictionResponse:
        try:
            stay_metadata = load_stay_metadata(stay_id)
        except KeyError:
            raise StayNotFoundError(f"Stay {stay_id} not found")
            
        validate_prediction_request(stay_id, prediction_time, stay_metadata)
        
        # 1. TRUNCATE HISTORY
        events = load_events(stay_id)
        truncated_events = truncate_history_at(events, prediction_time)
        
        # 2. FEATURE CONSTRUCTION
        features = self.feature_builder.build_features(truncated_events, prediction_time, stay_metadata)
        
        # 3. LOAD MANIFEST
        manifest = self.artifact_loader.load_model_manifest()
        tasks_config = manifest.get('tasks', {})
        
        # Deterministic seed for mock models
        seed_str = f'{stay_id}_{prediction_time.isoformat()}'
        seed_int = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed_int)
        
        task_metadata_dict = {}
        explanations_dict = {}
        
        # We need mock outputs since models are mock
        # For a real pipeline, we'd load the model_family artifact here
        
        # sofa_delta_24h
        t_24 = tasks_config.get('sofa_delta_24h', {})
        t_48 = tasks_config.get('sofa_delta_48h', {})
        t_icu = tasks_config.get('remaining_icu_time', {})
        t_org = tasks_config.get('organ_support_initiation', {})

        # Recovery
        pred_delta_24h = round(float(rng.uniform(-2, 3)), 1)
        pred_delta_48h = round(float(rng.uniform(-3, 5)), 1)
        # Mock current sofa from features
        current_sofa = 5.0
        rec_post = postprocess_recovery(current_sofa, pred_delta_24h, pred_delta_48h)
        recovery_pred = RecoveryPrediction(**rec_post)
        
        # ICU Time
        pred_icu_log1p = float(rng.uniform(1, 4))
        icu_post = postprocess_icu_stay_time(pred_icu_log1p)
        icu_pred = ICUStayTimePrediction(**icu_post)
        
        # Organ support
        pred_prob = float(rng.uniform(0, 1))
        threshold = t_org.get('threshold', 0.5)
        org_post = postprocess_organ_support(pred_prob, threshold=threshold)
        org_pred = OrganSupportPrediction(
            calibrated_probability=org_post['calibrated_probability'],
            threshold=org_post['threshold'],
            support_class=org_post['support_class']
        )
        
        predictions = Predictions(
            recovery=recovery_pred,
            icu_stay_time=icu_pred,
            organ_support=org_pred
        )
        
        for task_name, config in tasks_config.items():
            task_metadata_dict[task_name] = TaskMetadata(
                model_family=config.get('family', 'mock'),
                model_version=config.get('model_version', 'v1'),
                artifact_hash=config.get('model_hash', 'none'),
                feature_version='mock_v1',
                label_version='mock_v1',
                split_version='mock_v1',
                preprocessor_version=config.get('preprocessor_version', 'v1'),
                calibrator_version=config.get('calibration', 'none'),
                threshold_version='v1' if config.get('threshold') is not None else None
            )
            
            if include_explanations:
                # Use explanation router
                explanations_dict[task_name] = route_explanations(
                    task_name=task_name,
                    model_family=config.get('family', 'mock'),
                    model_hash=config.get('model_hash', 'none'),
                    prediction_cutoff=prediction_time,
                    features=features,
                    mock_rng=rng
                )

        data_quality = DataQuality(
            observed_bin_counts={"all": features.get('observed_bins', 6)},
            missingness_summaries={"all": {}},
            padding_indicators={"all": False},
            available_historical_information={"hours_since_admission": 24.0},
            feature_masks={"all": {}}
        )

        return PredictionResponse(
            schema_version='prediction_schema_v1',
            request=RequestEcho(stay_id=stay_id, prediction_time=prediction_time),
            predictions=predictions,
            explanations=explanations_dict if include_explanations else None,
            data_quality=data_quality,
            metadata=PredictionMetadata(
                global_pipeline_version=self.PIPELINE_VERSION,
                tasks=task_metadata_dict
            ),
            replay=ReplayInfo(
                mode='RETROSPECTIVE_SEQUENTIAL_REPLAY',
                future_data_used=False,
                history_truncated_at=prediction_time
            )
        )
