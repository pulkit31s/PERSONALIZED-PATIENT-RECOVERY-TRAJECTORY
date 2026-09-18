from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from enum import Enum
import logging

class SupportType(Enum):
    VASOPRESSOR = "VASOPRESSOR"
    INVASIVE_VENTILATION = "INVASIVE_VENTILATION"

class SupportStateValue(Enum):
    ON = "ON"
    OFF = "OFF"

@dataclass
class SupportInterval:
    """Represents an interval of medical support (e.g., vasopressor or ventilation)."""
    support_type: SupportType
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime]
    source: str = 'mock'
    provenance_version: str = 'event_dict_v1'
    
    def is_valid(self) -> bool:
        """Validates that the start time is present and end time is at or after start time."""
        if self.start_time is None:
            return False
        if self.end_time is None:
            return True
        return self.end_time >= self.start_time

    def is_active_at(self, t: datetime) -> bool:
        """Checks if the support interval is active at the given time t."""
        if not self.is_valid():
            return False
        if t < self.start_time:
            return False
        if self.end_time is not None and t > self.end_time:
            return False
        return True

@dataclass
class SupportState:
    """Represents the overall state of a specific support type at a given evaluation time."""
    support_type: SupportType
    state: SupportStateValue
    active_intervals: List[SupportInterval]
    evaluation_time: datetime
    source: str = 'mock'
    provenance_version: str = 'event_dict_v1'

QUALIFYING_VASOPRESSORS = frozenset({'norepinephrine', 'epinephrine', 'vasopressin', 'dopamine', 'phenylephrine'})

def get_vasopressor_state_at(events: List[SupportInterval], prediction_time: datetime) -> SupportState:
    """
    Evaluates the state of qualifying vasopressor support at a specific prediction time.
    """
    active = []
    for event in events:
        if event.support_type != SupportType.VASOPRESSOR:
            continue
        if event.agent_name not in QUALIFYING_VASOPRESSORS:
            continue
        if not event.is_valid():
            logging.warning(f"Invalid vasopressor interval skipped: {event}")
            continue
        if event.is_active_at(prediction_time):
            active.append(event)
            
    return SupportState(
        support_type=SupportType.VASOPRESSOR,
        state=SupportStateValue.ON if active else SupportStateValue.OFF,
        active_intervals=active,
        evaluation_time=prediction_time
    )
