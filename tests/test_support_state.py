from src.labels.support_state import (
    get_vasopressor_state_at, SupportStateValue, SupportType, SupportInterval, QUALIFYING_VASOPRESSORS
)
from datetime import timedelta
from src.mock.mock_data import BASE_TIME

def test_no_events(base_time):
    result = get_vasopressor_state_at([], base_time)
    assert result.state == SupportStateValue.OFF

def test_active_vasopressor(make_vaso_interval, base_time):
    interval = make_vaso_interval(0, 12)  # starts at base, ends at +12h
    result = get_vasopressor_state_at([interval], base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.ON
    assert len(result.active_intervals) == 1

def test_vasopressor_ended(make_vaso_interval, base_time):
    interval = make_vaso_interval(0, 5)  # 0h to 5h
    result = get_vasopressor_state_at([interval], base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.OFF

def test_vasopressor_not_started(make_vaso_interval, base_time):
    interval = make_vaso_interval(10, 20)  # 10h to 20h
    result = get_vasopressor_state_at([interval], base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.OFF

def test_exact_start_boundary(make_vaso_interval, base_time):
    interval = make_vaso_interval(6, 12)  # starts exactly at prediction
    result = get_vasopressor_state_at([interval], base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.ON  # start_time <= t

def test_exact_end_boundary(make_vaso_interval, base_time):
    interval = make_vaso_interval(0, 6)  # ends exactly at prediction
    result = get_vasopressor_state_at([interval], base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.ON  # end_time >= t

def test_ongoing_no_end(make_vaso_interval, base_time):
    interval = make_vaso_interval(0, None)  # no end time = ongoing
    result = get_vasopressor_state_at([interval], base_time + timedelta(hours=100))
    assert result.state == SupportStateValue.ON

def test_non_qualifying_agent(base_time):
    interval = SupportInterval(
        support_type=SupportType.VASOPRESSOR,
        agent_name='fake_drug_xyz',
        start_time=base_time,
        end_time=base_time + timedelta(hours=12),
    )
    result = get_vasopressor_state_at([interval], base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.OFF

def test_invalid_interval_skipped(base_time):
    interval = SupportInterval(
        support_type=SupportType.VASOPRESSOR,
        agent_name='norepinephrine',
        start_time=base_time + timedelta(hours=10),
        end_time=base_time + timedelta(hours=5),  # end before start!
    )
    result = get_vasopressor_state_at([interval], base_time + timedelta(hours=7))
    assert result.state == SupportStateValue.OFF

def test_multiple_overlapping(make_vaso_interval, base_time):
    intervals = [
        make_vaso_interval(0, 8, agent='norepinephrine'),
        make_vaso_interval(4, 12, agent='epinephrine'),
    ]
    result = get_vasopressor_state_at(intervals, base_time + timedelta(hours=6))
    assert result.state == SupportStateValue.ON
    assert len(result.active_intervals) == 2
