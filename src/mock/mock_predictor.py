# ALL DATA IS SYNTHETIC — NOT MIMIC-IV CLINICAL DATA
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import numpy as np
from src.schemas.prediction import (
    Predictions, SOFAPrediction, RemainingICUTimePrediction,
    OrganSupportPrediction, Explanations, ExplanationItem, DataQuality
)
import logging

class MockPredictor:
    """Generates deterministic mock predictions based on stable feature characteristics."""
    
    def __init__(self, manifest: Dict[str, Any]):
        """Initialize with model manifest configuration."""
        self.manifest = manifest
        
    def predict(
        self, 
        stay_id: str, 
        prediction_time: datetime, 
        features: Dict[str, Any], 
        include_explanations: bool = True
    ) -> Tuple[Predictions, Optional[Explanations], DataQuality]:
        """Generate a mock prediction."""
        
        # Create deterministic seed
        seed_str = f'{stay_id}_{prediction_time.isoformat()}'
        seed_hex = hashlib.md5(seed_str.encode()).hexdigest()[:8]
        seed_int = int(seed_hex, 16)
        rng = np.random.RandomState(seed_int)
        
        # Generate predictions
        sofa_delta_24h = round(float(rng.uniform(-2, 3)), 1)
        sofa_delta_48h = round(float(rng.uniform(-3, 5)), 1)
        remaining_icu_time = round(float(rng.uniform(2, 120)), 1)
        prob = round(float(rng.uniform(0, 1)), 3)
        
        threshold = self.manifest.get('tasks', {}).get('organ_support_initiation', {}).get('threshold', 0.5)
        alert = prob >= threshold
        monitored_types = self.manifest.get('tasks', {}).get('organ_support_initiation', {}).get('monitored_support_types', ['VASOPRESSOR', 'INVASIVE_VENT'])
        
        preds = Predictions(
            sofa_delta_24h=SOFAPrediction(value=sofa_delta_24h),
            sofa_delta_48h=SOFAPrediction(value=sofa_delta_48h),
            remaining_icu_time=RemainingICUTimePrediction(value=remaining_icu_time),
            organ_support_initiation=OrganSupportPrediction(
                probability=prob,
                threshold=threshold,
                alert=alert,
                monitored_support_types=monitored_types
            )
        )
        
        explanations = None
        if include_explanations:
            items = [
                ExplanationItem(
                    feature_name='heart_rate_trend',
                    contribution=round(float(rng.uniform(0.01, 0.2)), 3),
                    direction='positive' if rng.rand() > 0.5 else 'negative'
                ),
                ExplanationItem(
                    feature_name='lactate_level',
                    contribution=round(float(rng.uniform(0.01, 0.2)), 3),
                    direction='positive' if rng.rand() > 0.5 else 'negative'
                ),
                ExplanationItem(
                    feature_name='hours_since_admission',
                    contribution=round(float(rng.uniform(0.01, 0.2)), 3),
                    direction='positive' if rng.rand() > 0.5 else 'negative'
                )
            ]
            explanations = Explanations(
                status='mock',
                method='mock_feature_contribution',
                items=items
            )
            
        data_quality = DataQuality(
            observed_bin_count=features.get('observed_bins', 6),
            total_bin_count=8,
            is_mock_data=True
        )
        
        return preds, explanations, data_quality
