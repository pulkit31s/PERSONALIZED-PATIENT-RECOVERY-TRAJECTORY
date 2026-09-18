import pandas as pd
from datetime import datetime
from typing import Optional, List
from src.mock.mock_data import MOCK_STAYS, get_mock_events, get_mock_support_intervals
from src.labels.support_state import SupportInterval
import logging

def load_stay_metadata(stay_id: str) -> dict:
    """Load metadata for a given stay ID.
    
    Args:
        stay_id: The ICU stay identifier
        
    Returns:
        dict: Stay metadata including intime, outtime, etc.
        
    Raises:
        KeyError: If stay_id is not found
    """
    if stay_id not in MOCK_STAYS:
        raise KeyError(f"Stay ID {stay_id} not found in mock data.")
    return MOCK_STAYS[stay_id]

def load_events(stay_id: str) -> pd.DataFrame:
    """Load all mock events for a stay.
    
    Args:
        stay_id: The ICU stay identifier
        
    Returns:
        pd.DataFrame: Deterministically sorted events
    """
    df = get_mock_events(stay_id)
    df = df.sort_values(by=['event_time', 'event_name'])
    return df

def load_support_intervals(stay_id: str) -> List[SupportInterval]:
    """Load support intervals for a stay.
    
    Args:
        stay_id: The ICU stay identifier
        
    Returns:
        List[SupportInterval]: Support intervals
    """
    return get_mock_support_intervals(stay_id)

def truncate_history_at(events: pd.DataFrame, prediction_time: datetime) -> pd.DataFrame:
    """Truncate history to prevent temporal leakage.
    
    Args:
        events: The complete event history
        prediction_time: The cutoff time for prediction
        
    Returns:
        pd.DataFrame: Filtered and sorted events up to prediction_time
    """
    if events.empty:
        return pd.DataFrame(columns=events.columns)
    
    events_copy = events.copy()
    if not pd.api.types.is_datetime64_any_dtype(events_copy['event_time']):
        events_copy['event_time'] = pd.to_datetime(events_copy['event_time'])
        
    filtered = events_copy[events_copy['event_time'] <= prediction_time]
    filtered = filtered.sort_values(by=['event_time', 'event_name'])
    return filtered
