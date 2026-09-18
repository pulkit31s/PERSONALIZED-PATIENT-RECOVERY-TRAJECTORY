# ALL DATA IS SYNTHETIC — NOT MIMIC-IV CLINICAL DATA
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum

class PredictionRequest(BaseModel):
    stay_id: str = Field(min_length=1)
    prediction_time: datetime
    include_explanations: bool = True

    @field_validator('prediction_time')
    def validate_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("prediction_time must be timezone-aware")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "stay_id": "mock_stay_001",
                "prediction_time": "2026-01-01T12:00:00Z",
                "include_explanations": True
            }
        }
    }

class SOFAPrediction(BaseModel):
    value: float
    unit: str = 'SOFA points'

class RemainingICUTimePrediction(BaseModel):
    value: float
    unit: str = 'hours'

class OrganSupportPrediction(BaseModel):
    probability: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    alert: bool
    monitored_support_types: List[str]

class Predictions(BaseModel):
    sofa_delta_24h: SOFAPrediction
    sofa_delta_48h: SOFAPrediction
    remaining_icu_time: RemainingICUTimePrediction
    organ_support_initiation: OrganSupportPrediction

class ExplanationItem(BaseModel):
    feature_name: str
    contribution: float
    direction: str

class Explanations(BaseModel):
    status: str
    method: str
    items: List[ExplanationItem] = Field(default_factory=list)

class DataQuality(BaseModel):
    observed_bin_count: int
    total_bin_count: int
    missingness_summary: Dict[str, Any] = Field(default_factory=dict)
    is_mock_data: bool = True

class PredictionMetadata(BaseModel):
    model_config = {"protected_namespaces": ()}

    pipeline_version: str
    model_manifest_version: str
    feature_schema_version: str
    label_schema_version: str
    preprocessor_version: str
    model_hash: str

class ReplayInfo(BaseModel):
    mode: str = 'retrospective_sequential_replay'
    future_data_used: bool = False
    history_truncated_at: datetime

class RequestEcho(BaseModel):
    stay_id: str
    prediction_time: datetime

class PredictionResponse(BaseModel):
    schema_version: str = 'prediction_schema_v1'
    request: RequestEcho
    predictions: Predictions
    explanations: Optional[Explanations] = None
    data_quality: DataQuality
    metadata: PredictionMetadata
    replay: ReplayInfo
