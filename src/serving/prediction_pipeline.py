from datetime import datetime, timezone
from typing import Optional, Dict, Any
from src.serving.history import load_stay_metadata, load_events, load_support_intervals, truncate_history_at
from src.serving.feature_builder import MockFeatureBuilder, FeatureBuilderInterface
from src.serving.artifact_loader import ArtifactLoader
from src.serving.validation import (
    validate_prediction_request, StayNotFoundError, InvalidPredictionTimeError, ArtifactLoadError
)
from src.mock.mock_predictor import MockPredictor
from src.schemas.prediction import (
    PredictionResponse, RequestEcho, PredictionMetadata, ReplayInfo
)
import logging

class PredictionPipeline:
    """Pipeline for processing and generating predictions."""
    
    PIPELINE_VERSION = 'pipeline_v1'

    def __init__(self, artifacts_dir: Optional[str] = None, feature_builder: Optional[FeatureBuilderInterface] = None):
        """Initialize the prediction pipeline.
        
        Args:
            artifacts_dir: Optional path to artifacts directory
            feature_builder: Optional feature builder instance
        """
        self.artifact_loader = ArtifactLoader(artifacts_dir)
        self.feature_builder = feature_builder or MockFeatureBuilder()
        self._predictor: Optional[MockPredictor] = None
        self.logger = logging.getLogger(__name__)

    def _get_predictor(self) -> MockPredictor:
        """Lazy load the mock predictor."""
        if self._predictor is None:
            manifest = self.artifact_loader.load_model_manifest()
            self._predictor = MockPredictor(manifest)
        return self._predictor

    def predict(self, stay_id: str, prediction_time: datetime, include_explanations: bool = True) -> PredictionResponse:
        """Run the prediction pipeline for a stay.
        
        Args:
            stay_id: The ICU stay identifier
            prediction_time: The time at which to predict
            include_explanations: Whether to include feature explanations
            
        Returns:
            PredictionResponse: Complete response with predictions and metadata
            
        Raises:
            StayNotFoundError: If stay doesn't exist
            InvalidPredictionTimeError: If prediction time is invalid
        """
        try:
            stay_metadata = load_stay_metadata(stay_id)
        except KeyError:
            raise StayNotFoundError(f"Stay {stay_id} not found")
            
        validate_prediction_request(stay_id, prediction_time, stay_metadata)
        
        events = load_events(stay_id)
        truncated_events = truncate_history_at(events, prediction_time)
        
        features = self.feature_builder.build_features(truncated_events, prediction_time, stay_metadata)
        
        predictor = self._get_predictor()
        predictions, explanations, data_quality = predictor.predict(
            stay_id, prediction_time, features, include_explanations
        )
        
        manifest = self.artifact_loader.load_model_manifest()
        
        return PredictionResponse(
            schema_version='prediction_schema_v1',
            request=RequestEcho(stay_id=stay_id, prediction_time=prediction_time),
            predictions=predictions,
            explanations=explanations if include_explanations else None,
            data_quality=data_quality,
            metadata=PredictionMetadata(
                pipeline_version=self.PIPELINE_VERSION,
                model_manifest_version=manifest.get('manifest_version', 'v1'),
                feature_schema_version='feature_schema_v1',
                label_schema_version='event_dict_v1',
                preprocessor_version='mock_preprocessor_v1',
                model_hash=self.artifact_loader.get_model_hash()
            ),
            replay=ReplayInfo(
                mode='retrospective_sequential_replay',
                future_data_used=False,
                history_truncated_at=prediction_time
            )
        )
