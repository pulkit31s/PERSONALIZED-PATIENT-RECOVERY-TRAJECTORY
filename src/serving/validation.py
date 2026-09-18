from datetime import datetime, timezone
from typing import Dict, Any
import logging

class StayNotFoundError(Exception):
    """Exception raised when an ICU stay is not found."""
    pass

class InvalidPredictionTimeError(Exception):
    """Exception raised when the prediction time is invalid."""
    pass
    
class ArtifactLoadError(Exception):
    """Exception raised when an artifact cannot be loaded."""
    pass

class ArtifactMismatchError(Exception):
    """Exception raised when artifacts are incompatible."""
    pass

def validate_prediction_request(stay_id: str, prediction_time: datetime, stay_metadata: dict) -> None:
    """Validate a prediction request against stay metadata.
    
    Args:
        stay_id: The ICU stay identifier
        prediction_time: The requested prediction time
        stay_metadata: Dictionary of stay metadata
        
    Raises:
        InvalidPredictionTimeError: If prediction time is naive or out of bounds
    """
    if prediction_time.tzinfo is None:
        raise InvalidPredictionTimeError("Prediction time must be timezone-aware.")
        
    intime = stay_metadata.get('intime')
    outtime = stay_metadata.get('outtime')
    
    if intime and prediction_time < intime:
        raise InvalidPredictionTimeError("Prediction time is before ICU admission")
        
    if outtime and prediction_time > outtime:
        raise InvalidPredictionTimeError("Prediction time is after ICU discharge")
