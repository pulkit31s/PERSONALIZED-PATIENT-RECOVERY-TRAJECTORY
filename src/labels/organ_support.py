from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from enum import Enum
import logging

from src.labels.support_state import (
    SupportInterval, SupportType, SupportStateValue,
    get_vasopressor_state_at, QUALIFYING_VASOPRESSORS
)
from src.labels.ventilation_state import (
    get_invasive_ventilation_state_at, QUALIFYING_VENTILATION_TYPES,
    VentilationType
)

class LabelStatus(Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    CENSORED = "CENSORED"
    INELIGIBLE = "INELIGIBLE"

@dataclass
class OrganSupportLabel:
    """Represents the organ support initiation label derived from support intervals."""
    label: Optional[bool]
    status: LabelStatus
    eligible: bool
    event_time: Optional[datetime]
    event_type: Optional[str]
    active_vasopressor_at_cutoff: bool
    active_ventilation_at_cutoff: bool
    censoring_time: Optional[datetime]
    censoring_reason: Optional[str]
    horizon_end: datetime
    follow_up_hours: Optional[float]
    provenance_version: str = 'event_dict_v1'

PREDICTION_HORIZON_HOURS = 24

def label_organ_support_initiation(
    events: List[SupportInterval], 
    prediction_time: datetime, 
    icu_outtime: Optional[datetime]
) -> OrganSupportLabel:
    """
    Computes the organ support initiation label (positive, negative, censored, ineligible).
    Evaluates new initiations strictly in (prediction_time, horizon_end].
    """
    # 1. Compute horizon_end
    horizon_end = prediction_time + timedelta(hours=PREDICTION_HORIZON_HOURS)
    
    # 2 & 3. Get states at prediction_time
    vaso_state = get_vasopressor_state_at(events, prediction_time)
    vent_state = get_invasive_ventilation_state_at(events, prediction_time)
    
    # 4 & 5. Check ON states
    vaso_on = vaso_state.state == SupportStateValue.ON
    vent_on = vent_state.state == SupportStateValue.ON
    
    # 6. If BOTH are ON -> INELIGIBLE
    if vaso_on and vent_on:
        return OrganSupportLabel(
            label=None,
            status=LabelStatus.INELIGIBLE,
            eligible=False,
            event_time=None,
            event_type=None,
            active_vasopressor_at_cutoff=vaso_on,
            active_ventilation_at_cutoff=vent_on,
            censoring_time=None,
            censoring_reason=None,
            horizon_end=horizon_end,
            follow_up_hours=0.0
        )
        
    # 7. Determine eligible components
    eligible_vaso = not vaso_on
    eligible_vent = not vent_on
    
    earliest_event_time = None
    earliest_event_type = None
    
    # 8. Search for OFF->ON transitions in (prediction_time, horizon_end]
    if eligible_vaso:
        for ev in events:
            if ev.support_type != SupportType.VASOPRESSOR:
                continue
            if ev.agent_name not in QUALIFYING_VASOPRESSORS:
                continue
            if not ev.is_valid():
                logging.warning(f"Invalid vasopressor interval skipped: {ev}")
                continue
            
            if prediction_time < ev.start_time <= horizon_end:
                if earliest_event_time is None or ev.start_time < earliest_event_time:
                    earliest_event_time = ev.start_time
                    earliest_event_type = 'vasopressor'

    if eligible_vent:
        qualifying_vent_names = {vt.value for vt in QUALIFYING_VENTILATION_TYPES}
        for ev in events:
            if ev.support_type != SupportType.INVASIVE_VENTILATION:
                continue
            if ev.agent_name not in qualifying_vent_names:
                continue
            if not ev.is_valid():
                logging.warning(f"Invalid ventilation interval skipped: {ev}")
                continue
                
            if prediction_time < ev.start_time <= horizon_end:
                if earliest_event_time is None or ev.start_time < earliest_event_time:
                    earliest_event_time = ev.start_time
                    earliest_event_type = 'invasive_ventilation'
                    
    # 10. Determine effective follow-up end
    if icu_outtime is not None:
        effective_end = min(horizon_end, icu_outtime)
    else:
        effective_end = horizon_end
        
    follow_up_hours = (effective_end - prediction_time).total_seconds() / 3600.0
    
    # 11. Decision logic
    if earliest_event_time is not None and earliest_event_time <= effective_end:
        return OrganSupportLabel(
            label=True,
            status=LabelStatus.POSITIVE,
            eligible=True,
            event_time=earliest_event_time,
            event_type=earliest_event_type,
            active_vasopressor_at_cutoff=vaso_on,
            active_ventilation_at_cutoff=vent_on,
            censoring_time=None,
            censoring_reason=None,
            horizon_end=horizon_end,
            follow_up_hours=follow_up_hours
        )
    else:
        # No qualifying initiation found or it was strictly after effective_end
        if icu_outtime is None or icu_outtime >= horizon_end:
            return OrganSupportLabel(
                label=False,
                status=LabelStatus.NEGATIVE,
                eligible=True,
                event_time=None,
                event_type=None,
                active_vasopressor_at_cutoff=vaso_on,
                active_ventilation_at_cutoff=vent_on,
                censoring_time=None,
                censoring_reason=None,
                horizon_end=horizon_end,
                follow_up_hours=follow_up_hours
            )
        else:
            return OrganSupportLabel(
                label=None,
                status=LabelStatus.CENSORED,
                eligible=True,
                event_time=None,
                event_type=None,
                active_vasopressor_at_cutoff=vaso_on,
                active_ventilation_at_cutoff=vent_on,
                censoring_time=icu_outtime,
                censoring_reason='icu_exit_before_horizon',
                horizon_end=horizon_end,
                follow_up_hours=follow_up_hours
            )
