import pandas as pd
from datetime import datetime, timezone, timedelta
from src.serving.history import truncate_history_at
from src.mock.mock_data import BASE_TIME, get_mock_events

def test_future_events_excluded():
    t = BASE_TIME + timedelta(hours=6)
    events = get_mock_events('mock_stay_001')
    truncated = truncate_history_at(events, t)
    assert all(truncated['event_time'] <= t)

def test_events_at_cutoff_included():
    # Create an event exactly at the cutoff
    t = BASE_TIME + timedelta(hours=6)
    df = pd.DataFrame([{
        'stay_id': 'test', 'event_time': t,
        'event_type': 'vital', 'event_name': 'hr', 'value': 80, 'unit': 'bpm'
    }])
    truncated = truncate_history_at(df, t)
    assert len(truncated) == 1

def test_original_not_mutated():
    events = get_mock_events('mock_stay_001')
    original_len = len(events)
    t = BASE_TIME + timedelta(hours=6)
    _ = truncate_history_at(events, t)
    assert len(events) == original_len  # original unchanged

def test_empty_input():
    df = pd.DataFrame(columns=['stay_id', 'event_time', 'event_type', 'event_name', 'value', 'unit'])
    result = truncate_history_at(df, BASE_TIME)
    assert result.empty
    assert list(result.columns) == list(df.columns)

def test_deterministic_ordering():
    events = get_mock_events('mock_stay_001')
    t = BASE_TIME + timedelta(hours=24)
    r1 = truncate_history_at(events, t)
    r2 = truncate_history_at(events, t)
    pd.testing.assert_frame_equal(r1.reset_index(drop=True), r2.reset_index(drop=True))

def test_modifying_future_does_not_affect_truncated():
    events = get_mock_events('mock_stay_001')
    t = BASE_TIME + timedelta(hours=12)
    truncated_before = truncate_history_at(events, t)
    # Remove future events from original
    events_modified = events[events['event_time'] > t + timedelta(hours=6)].copy()
    events_combined = pd.concat([events[events['event_time'] <= t], events_modified], ignore_index=True)
    truncated_after = truncate_history_at(events_combined, t)
    pd.testing.assert_frame_equal(
        truncated_before.reset_index(drop=True),
        truncated_after.reset_index(drop=True)
    )

def test_48h_lookback_boundary():
    # Events more than 48h before prediction should still be included (truncation is about future, not past)
    t = BASE_TIME + timedelta(hours=60)
    old_event_time = BASE_TIME  # 60h before prediction
    df = pd.DataFrame([{
        'stay_id': 'test', 'event_time': old_event_time,
        'event_type': 'vital', 'event_name': 'hr', 'value': 80, 'unit': 'bpm'
    }, {
        'stay_id': 'test', 'event_time': t + timedelta(hours=1),
        'event_type': 'vital', 'event_name': 'hr', 'value': 90, 'unit': 'bpm'
    }])
    truncated = truncate_history_at(df, t)
    assert len(truncated) == 1  # only the old event, not the future one
