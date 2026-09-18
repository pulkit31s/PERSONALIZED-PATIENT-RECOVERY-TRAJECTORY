from typing import Dict, Any
from datetime import datetime
from src.schemas.prediction import TaskExplanation
from src.explainability.ig import generate_ig_explanations
from src.explainability.tree_shap import generate_tree_shap_explanations

def route_explanations(
    task_name: str,
    model_family: str,
    model_hash: str,
    prediction_cutoff: datetime,
    features: Dict[str, Any],
    mock_rng
) -> TaskExplanation:
    """Route explanation generation based on model family."""
    
    if model_family.lower() == 'xgboost':
        items = generate_tree_shap_explanations(model_hash, prediction_cutoff, features, mock_rng)
        method = 'TreeSHAP'
    elif model_family.lower() == 'gru':
        items = generate_ig_explanations(model_hash, prediction_cutoff, features, mock_rng)
        method = 'IntegratedGradients'
    else:
        raise ValueError(f"Unknown or unsupported model family for explanation: {model_family}")
        
    return TaskExplanation(
        status='success',
        method=method,
        model_hash=model_hash,
        prediction_cutoff=prediction_cutoff,
        items=items
    )
