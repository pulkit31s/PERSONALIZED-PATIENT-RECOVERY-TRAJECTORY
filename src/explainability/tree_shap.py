from typing import Dict, Any, List
from datetime import datetime
from src.schemas.prediction import ExplanationItem

def generate_tree_shap_explanations(
    model_hash: str,
    prediction_cutoff: datetime,
    features: Dict[str, Any],
    mock_rng
) -> List[ExplanationItem]:
    """TreeSHAP for XGBoost"""
    # Deterministic mock TreeSHAP explanations
    items = []
    for i in range(3):
        items.append(
            ExplanationItem(
                feature_name=f'mock_feature_{i}',
                time_bin='bin_0',
                feature_value=round(float(mock_rng.uniform(0, 5)), 3),
                contribution=round(float(mock_rng.uniform(0.01, 0.2)), 3),
                direction='positive' if mock_rng.rand() > 0.5 else 'negative'
            )
        )
    return items
