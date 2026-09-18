from src.labels.ventilation_state import get_invasive_ventilation_state_at, VentilationType
from src.labels.support_state import SupportStateValue, SupportType, SupportInterval
from datetime import timedelta
from src.mock.mock_data import BASE_TIME

def test_invasive_active(make_vent_interval, base_time):
    interval = make_vent_interval(0, 12, vent_type='invasive_mechanical_ventilation')
    result = get_invasive_ventilation_state_at([interval], base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.ON

def test_niv_not_qualifying(make_vent_interval, base_time):
    interval = make_vent_interval(0, 12, vent_type='non_invasive_ventilation')
    result = get_invasive_ventilation_state_at([interval], base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.OFF

def test_hfnc_not_qualifying(make_vent_interval, base_time):
    interval = make_vent_interval(0, 12, vent_type='high_flow_nasal_cannula')
    result = get_invasive_ventilation_state_at([interval], base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.OFF

def test_generic_o2_not_qualifying(make_vent_interval, base_time):
    interval = make_vent_interval(0, 12, vent_type='generic_oxygen_support')
    result = get_invasive_ventilation_state_at([interval], base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.OFF

def test_invasive_ended(make_vent_interval, base_time):
    interval = make_vent_interval(0, 5)
    result = get_invasive_ventilation_state_at([interval], base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.OFF

def test_no_events(base_time):
    result = get_invasive_ventilation_state_at([], base_time)
    assert result.state == SupportStateValue.OFF
