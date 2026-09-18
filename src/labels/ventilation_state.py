from enum import Enum
from typing import List
from datetime import datetime
import logging

from src.labels.support_state import SupportInterval, SupportState, SupportType, SupportStateValue

class VentilationType(Enum):
    INVASIVE_MECHANICAL_VENTILATION = "invasive_mechanical_ventilation"
    NON_INVASIVE_VENTILATION = "non_invasive_ventilation"
    HIGH_FLOW_NASAL_CANNULA = "high_flow_nasal_cannula"
    GENERIC_OXYGEN_SUPPORT = "generic_oxygen_support"

QUALIFYING_VENTILATION_TYPES = frozenset({VentilationType.INVASIVE_MECHANICAL_VENTILATION})
NON_QUALIFYING_VENTILATION_TYPES = frozenset({
    VentilationType.NON_INVASIVE_VENTILATION, 
    VentilationType.HIGH_FLOW_NASAL_CANNULA, 
    VentilationType.GENERIC_OXYGEN_SUPPORT
})

def get_invasive_ventilation_state_at(events: List[SupportInterval], prediction_time: datetime) -> SupportState:
    """
    Evaluates the state of qualifying invasive ventilation support at a specific prediction time.
    """
    active = []
    qualifying_agent_names = {vt.value for vt in QUALIFYING_VENTILATION_TYPES}
    
    for event in events:
        if event.support_type != SupportType.INVASIVE_VENTILATION:
            continue
        if event.agent_name not in qualifying_agent_names:
            continue
        if not event.is_valid():
            logging.warning(f"Invalid ventilation interval skipped: {event}")
            continue
        if event.is_active_at(prediction_time):
            active.append(event)
            
    return SupportState(
        support_type=SupportType.INVASIVE_VENTILATION,
        state=SupportStateValue.ON if active else SupportStateValue.OFF,
        active_intervals=active,
        evaluation_time=prediction_time
    )
