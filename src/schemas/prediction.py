# ALL DATA IS SYNTHETIC — NOT MIMIC-IV CLINICAL DATA
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

class PredictionRequest(BaseModel):
    stay_id: str = Field(min_length=1)
    prediction_time: datetime
    include_explanations: bool = True

    @field_validator('prediction_time')
    def validate_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("prediction_time must be timezone-aware")
        return v

class RecoveryPrediction(BaseModel):
    delta_24h: float
    delta_48h: float
    reconstructed_sofa_24h: float
    reconstructed_sofa_48h: float

class ICUStayTimePrediction(BaseModel):
    remaining_hours: float
    
class OrganSupportPrediction(BaseModel):
    calibrated_probability: float = Field(ge=0.0, le=1.0)
    threshold: Optional[float] = None
    support_class: Optional[bool] = None

class Predictions(BaseModel):
    recovery: RecoveryPrediction
    icu_stay_time: ICUStayTimePrediction
    organ_support: OrganSupportPrediction

class ExplanationItem(BaseModel):
    feature_name: str
    time_bin: Optional[str] = None
    timestep: Optional[int] = None
    feature_value: Optional[float] = None
    contribution: float
    direction: str

class TaskExplanation(BaseModel):
    model_config = {"protected_namespaces": ()}
    status: str
    method: str
    model_hash: str
    prediction_cutoff: datetime
    items: List[ExplanationItem] = Field(default_factory=list)

class DataQuality(BaseModel):
    observed_bin_counts: Dict[str, int] = Field(default_factory=dict)
    missingness_summaries: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    padding_indicators: Dict[str, bool] = Field(default_factory=dict)
    available_historical_information: Dict[str, Any] = Field(default_factory=dict)
    feature_masks: Dict[str, Any] = Field(default_factory=dict)

class TaskMetadata(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_family: str
    model_version: str
    artifact_hash: str
    feature_version: str
    label_version: str
    split_version: str
    preprocessor_version: str
    calibrator_version: Optional[str] = None
    threshold_version: Optional[str] = None

class PredictionMetadata(BaseModel):
    model_config = {"protected_namespaces": ()}
    global_pipeline_version: str
    tasks: Dict[str, TaskMetadata]

class ReplayInfo(BaseModel):
    mode: str = 'RETROSPECTIVE_SEQUENTIAL_REPLAY'
    future_data_used: bool = False
    history_truncated_at: datetime

class RequestEcho(BaseModel):
    stay_id: str
    prediction_time: datetime

class PredictionResponse(BaseModel):
    schema_version: str = 'prediction_schema_v1'
    request: RequestEcho
    predictions: Predictions
    explanations: Optional[Dict[str, TaskExplanation]] = None
    data_quality: DataQuality
    metadata: PredictionMetadata
    replay: ReplayInfo
