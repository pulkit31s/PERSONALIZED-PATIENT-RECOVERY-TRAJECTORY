import numpy as np

def postprocess_recovery(current_sofa: float, predicted_delta_24h: float, predicted_delta_48h: float):
    # Do not chain the two predicted deltas.
    sofa_at_24 = current_sofa + predicted_delta_24h
    sofa_at_48 = current_sofa + predicted_delta_48h
    return {
        "delta_24h": predicted_delta_24h,
        "delta_48h": predicted_delta_48h,
        "reconstructed_sofa_24h": sofa_at_24,
        "reconstructed_sofa_48h": sofa_at_48
    }

def postprocess_icu_stay_time(predicted_log1p: float):
    # Correctly inverse-transform log1p output
    remaining_hours = np.expm1(predicted_log1p)
    # Never return negative time
    remaining_hours = max(0.0, remaining_hours)
    return {
        "remaining_hours": remaining_hours
    }

def postprocess_organ_support(raw_probability: float, threshold: float = None, calibrator=None):
    # Use the validation-fitted calibrator if available
    if calibrator is not None:
        calibrated_probability = calibrator(raw_probability)
    else:
        calibrated_probability = raw_probability
        
    support_class = None
    if threshold is not None:
        support_class = calibrated_probability >= threshold
        
    return {
        "calibrated_probability": calibrated_probability,
        "threshold": threshold,
        "support_class": support_class
    }
