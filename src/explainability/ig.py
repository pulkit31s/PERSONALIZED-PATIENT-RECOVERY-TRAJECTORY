from typing import Dict, Any, List
from datetime import datetime
from src.schemas.prediction import ExplanationItem

def generate_ig_explanations(
    model_hash: str,
    prediction_cutoff: datetime,
    features: Dict[str, Any],
    mock_rng
) -> List[ExplanationItem]:
    """Integrated Gradients for GRU"""
    # Deterministic mock IG explanations
    items = []
    # GRU has timesteps
    for i in range(3):
        items.append(
            ExplanationItem(
                feature_name=f'mock_feature_{i}',
                timestep=int(mock_rng.randint(0, 10)),
                feature_value=round(float(mock_rng.uniform(0, 5)), 3),
                contribution=round(float(mock_rng.uniform(0.01, 0.2)), 3),
                direction='positive' if mock_rng.rand() > 0.5 else 'negative'
            )
        )
    return items
