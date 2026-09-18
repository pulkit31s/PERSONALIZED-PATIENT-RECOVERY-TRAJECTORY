import pytest
from datetime import datetime, timezone, timedelta
from src.labels.support_state import SupportInterval, SupportType
from src.mock.mock_data import BASE_TIME

@pytest.fixture
def base_time():
    return BASE_TIME

@pytest.fixture
def prediction_time(base_time):
    return base_time + timedelta(hours=6)

@pytest.fixture
def make_vaso_interval():
    def _make(start_offset_h, end_offset_h=None, agent='norepinephrine', base=None):
        base = base or BASE_TIME
        return SupportInterval(
            support_type=SupportType.VASOPRESSOR,
            agent_name=agent,
            start_time=base + timedelta(hours=start_offset_h),
            end_time=base + timedelta(hours=end_offset_h) if end_offset_h is not None else None,
        )
    return _make

@pytest.fixture
def make_vent_interval():
    def _make(start_offset_h, end_offset_h=None, vent_type='invasive_mechanical_ventilation', base=None):
        base = base or BASE_TIME
        return SupportInterval(
            support_type=SupportType.INVASIVE_VENTILATION,
            agent_name=vent_type,
            start_time=base + timedelta(hours=start_offset_h),
            end_time=base + timedelta(hours=end_offset_h) if end_offset_h is not None else None,
        )
    return _make
