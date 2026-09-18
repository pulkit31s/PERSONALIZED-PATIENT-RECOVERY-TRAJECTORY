from src.labels.organ_support import label_organ_support_initiation, LabelStatus, PREDICTION_HORIZON_HOURS
from src.labels.support_state import SupportInterval, SupportType
from datetime import timedelta, datetime, timezone
from src.mock.mock_data import BASE_TIME

T = BASE_TIME + timedelta(hours=6)  # prediction time

# Case 1: Already ON - vasopressor starts before cutoff, continues after
def test_case1_already_on(make_vaso_interval):
    interval = make_vaso_interval(0, 48)  # covers cutoff
    result = label_organ_support_initiation([interval], T, T + timedelta(hours=48))
    # Vasopressor is ON at cutoff. Ventilation is OFF.
    # With only vaso ON, vent is still eligible. But no vent initiation.
    assert result.active_vasopressor_at_cutoff is True
    # Since ventilation is OFF and no vent event, depends on follow-up

# Case 2: OFF->ON positive
def test_case2_off_on_positive(make_vaso_interval):
    interval = make_vaso_interval(10, 20)  # starts at base+10h, which is T+4h (within 24h)
    result = label_organ_support_initiation([interval], T, T + timedelta(hours=48))
    assert result.label is True
    assert result.status == LabelStatus.POSITIVE
    assert result.event_type == 'vasopressor'

# Case 3: Negative (no support, complete follow-up)
def test_case3_negative():
    result = label_organ_support_initiation([], T, T + timedelta(hours=48))
    assert result.label is False
    assert result.status == LabelStatus.NEGATIVE
    assert result.eligible is True

# Case 4: Censored (ICU exit at T+8h, no event)
def test_case4_censored():
    result = label_organ_support_initiation([], T, T + timedelta(hours=8))
    assert result.label is None
    assert result.status == LabelStatus.CENSORED
    assert result.censoring_reason == 'icu_exit_before_horizon'

# Case 5: Positive before censoring (event at T+4h, ICU exit at T+8h)
def test_case5_positive_before_censoring(make_vaso_interval):
    # Vaso starts at T+4h = base+10h
    interval = make_vaso_interval(10, 14)  # T+4h to T+8h
    result = label_organ_support_initiation([interval], T, T + timedelta(hours=8))
    assert result.label is True
    assert result.status == LabelStatus.POSITIVE

# Case 6: Invasive ventilation only
def test_case6_invasive_ventilation_only(make_vent_interval):
    interval = make_vent_interval(10, 20)  # starts at T+4h, invasive
    result = label_organ_support_initiation([interval], T, T + timedelta(hours=48))
    assert result.label is True
    assert result.status == LabelStatus.POSITIVE
    assert result.event_type == 'invasive_ventilation'

# Case 7: Non-invasive ventilation only (NOT positive)
def test_case7_niv_only(make_vent_interval):
    interval = make_vent_interval(10, 20, vent_type='non_invasive_ventilation')
    result = label_organ_support_initiation([interval], T, T + timedelta(hours=48))
    assert result.label is False
    assert result.status == LabelStatus.NEGATIVE

# Case 8: Dual components - one ON, one OFF
def test_case8_dual_components(make_vaso_interval, make_vent_interval):
    vaso = make_vaso_interval(0, 48)  # ON at cutoff
    vent = make_vent_interval(10, 20)  # starts at T+4h, invasive (OFF at cutoff)
    result = label_organ_support_initiation([vaso, vent], T, T + timedelta(hours=48))
    assert result.label is True
    assert result.status == LabelStatus.POSITIVE
    assert result.event_type == 'invasive_ventilation'
    assert result.active_vasopressor_at_cutoff is True

# Case 9: Exact boundary - event exactly at T (not new initiation)
def test_case9_exact_at_cutoff(make_vaso_interval):
    # Starts exactly at T = base+6h
    interval = make_vaso_interval(6, 12)
    result = label_organ_support_initiation([interval], T, T + timedelta(hours=48))
    # At T, this interval is active -> vasopressor is ON -> not a new initiation
    assert result.active_vasopressor_at_cutoff is True
    # Ventilation is OFF, no vent event -> negative (with full follow-up)
    assert result.status == LabelStatus.NEGATIVE

# Case 9b: Event exactly at horizon end T+24h (inclusive)
def test_case9b_exact_at_horizon_end(make_vaso_interval):
    interval = make_vaso_interval(30, 36)  # starts at base+30h = T+24h exactly
    result = label_organ_support_initiation([interval], T, T + timedelta(hours=48))
    assert result.label is True  # horizon is (T, T+24h] so T+24h is INCLUDED
    assert result.status == LabelStatus.POSITIVE

# Case 10: Invalid interval (end before start)
def test_case10_invalid_interval():
    invalid = SupportInterval(
        support_type=SupportType.VASOPRESSOR,
        agent_name='norepinephrine',
        start_time=BASE_TIME + timedelta(hours=10),
        end_time=BASE_TIME + timedelta(hours=5),  # INVALID: end before start
    )
    result = label_organ_support_initiation([invalid], T, T + timedelta(hours=48))
    # Invalid interval should be skipped, so negative
    assert result.label is False
    assert result.status == LabelStatus.NEGATIVE

# Case: Both ON -> ineligible
def test_both_on_ineligible(make_vaso_interval, make_vent_interval):
    vaso = make_vaso_interval(0, 48)  # ON at cutoff
    vent = make_vent_interval(0, 48)  # ON at cutoff (invasive)
    result = label_organ_support_initiation([vaso, vent], T, T + timedelta(hours=48))
    assert result.label is None
    assert result.status == LabelStatus.INELIGIBLE
    assert result.eligible is False
