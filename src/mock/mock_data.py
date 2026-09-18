# ALL DATA IS SYNTHETIC — NOT MIMIC-IV CLINICAL DATA
"""
Synthetic ICU data for development and testing.
All patient data is fabricated. This is NOT MIMIC-IV clinical data.
Do not use for clinical decision-making.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List
import os
import logging

from src.labels.support_state import SupportInterval, SupportType

logger = logging.getLogger(__name__)

BASE_TIME = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'data', 'demo'
)

# ---------------------------------------------------------------------------
# Mock ICU stays
# ---------------------------------------------------------------------------
MOCK_STAYS: Dict[str, dict] = {
    'mock_stay_001': {
        'subject_id': 'subj_001', 'hadm_id': 'hadm_001',
        'intime': BASE_TIME,
        'outtime': BASE_TIME + timedelta(hours=72),
    },
    'mock_stay_002': {
        # Short stay (8 h) — for censoring / positive-before-censoring tests
        'subject_id': 'subj_002', 'hadm_id': 'hadm_002',
        'intime': BASE_TIME + timedelta(hours=24),
        'outtime': BASE_TIME + timedelta(hours=32),
    },
    'mock_stay_003': {
        # Vasopressor starts 6 h after admission
        'subject_id': 'subj_003', 'hadm_id': 'hadm_003',
        'intime': BASE_TIME,
        'outtime': BASE_TIME + timedelta(hours=48),
    },
    'mock_stay_004': {
        # Invasive ventilation starts 10 h after admission
        'subject_id': 'subj_004', 'hadm_id': 'hadm_004',
        'intime': BASE_TIME,
        'outtime': BASE_TIME + timedelta(hours=96),
    },
    'mock_stay_005': {
        # Both vasopressor AND invasive vent running from admission
        'subject_id': 'subj_005', 'hadm_id': 'hadm_005',
        'intime': BASE_TIME,
        'outtime': BASE_TIME + timedelta(hours=120),
    },
    'mock_stay_006': {
        # NIV only (non-qualifying ventilation)
        'subject_id': 'subj_006', 'hadm_id': 'hadm_006',
        'intime': BASE_TIME,
        'outtime': BASE_TIME + timedelta(hours=48),
    },
}


def get_mock_stays() -> pd.DataFrame:
    """Return a DataFrame of all synthetic ICU stays."""
    rows = []
    for stay_id, data in MOCK_STAYS.items():
        rows.append({
            'stay_id': stay_id,
            'subject_id': data['subject_id'],
            'hadm_id': data['hadm_id'],
            'intime': data['intime'],
            'outtime': data['outtime'],
        })
    return pd.DataFrame(rows)


def get_mock_events(stay_id: str) -> pd.DataFrame:
    """Generate deterministic mock vitals and labs for *stay_id*.

    Uses a fixed numpy RandomState seeded on the stay_id hash so repeated
    calls return identical data.
    """
    if stay_id not in MOCK_STAYS:
        return pd.DataFrame(columns=[
            'stay_id', 'event_time', 'event_type', 'event_name', 'value', 'unit'
        ])

    stay = MOCK_STAYS[stay_id]
    intime = stay['intime']
    outtime = stay['outtime']
    duration_hours = int((outtime - intime).total_seconds() / 3600)

    seed = int(hash(stay_id) % (2**31))
    rng = np.random.RandomState(seed)

    events = []
    hour = 0
    while hour < duration_hours:
        event_time = intime + timedelta(hours=hour)
        events.append((stay_id, event_time, 'vital', 'heart_rate',
                        round(float(rng.normal(80, 15)), 1), 'bpm'))
        events.append((stay_id, event_time, 'vital', 'sbp',
                        round(float(rng.normal(120, 20)), 1), 'mmHg'))
        events.append((stay_id, event_time, 'vital', 'dbp',
                        round(float(rng.normal(75, 12)), 1), 'mmHg'))
        events.append((stay_id, event_time, 'vital', 'spo2',
                        round(float(rng.normal(96, 3)), 1), 'percent'))
        events.append((stay_id, event_time, 'vital', 'resp_rate',
                        round(float(rng.normal(18, 4)), 1), 'breaths_per_min'))
        events.append((stay_id, event_time, 'vital', 'temperature',
                        round(float(rng.normal(37.0, 0.5)), 2), 'celsius'))
        events.append((stay_id, event_time, 'lab', 'lactate',
                        round(abs(float(rng.normal(2.0, 1.0))), 2), 'mmol_per_L'))
        events.append((stay_id, event_time, 'lab', 'creatinine',
                        round(abs(float(rng.normal(1.0, 0.5))), 2), 'mg_per_dL'))
        events.append((stay_id, event_time, 'lab', 'wbc',
                        round(abs(float(rng.normal(10.0, 4.0))), 1), 'K_per_uL'))
        events.append((stay_id, event_time, 'lab', 'platelets',
                        round(abs(float(rng.normal(200, 80))), 0), 'K_per_uL'))
        step = int(rng.randint(1, 7))
        hour += step

    return pd.DataFrame(events, columns=[
        'stay_id', 'event_time', 'event_type', 'event_name', 'value', 'unit'
    ])


def get_mock_support_intervals(stay_id: str) -> List[SupportInterval]:
    """Return deterministic support intervals for *stay_id*.

    Mapping:
      mock_stay_001 — No support (clean negative case)
      mock_stay_002 — Vasopressor starts 4 h after admission (positive-before-censoring)
      mock_stay_003 — Norepinephrine from intime+6 h to intime+18 h
      mock_stay_004 — Invasive ventilation from intime+10 h to intime+36 h
      mock_stay_005 — Both vasopressor AND invasive vent from admission (ongoing)
      mock_stay_006 — NIV only from intime+3 h (non-qualifying)
    """
    if stay_id not in MOCK_STAYS:
        return []

    intime = MOCK_STAYS[stay_id]['intime']
    intervals: List[SupportInterval] = []

    if stay_id == 'mock_stay_001':
        pass  # no support

    elif stay_id == 'mock_stay_002':
        # Vasopressor at intime+4 h, ends at intime+8 h
        intervals.append(SupportInterval(
            support_type=SupportType.VASOPRESSOR,
            agent_name='norepinephrine',
            start_time=intime + timedelta(hours=4),
            end_time=intime + timedelta(hours=8),
        ))

    elif stay_id == 'mock_stay_003':
        # Norepinephrine from intime+6 h to intime+18 h
        intervals.append(SupportInterval(
            support_type=SupportType.VASOPRESSOR,
            agent_name='norepinephrine',
            start_time=intime + timedelta(hours=6),
            end_time=intime + timedelta(hours=18),
        ))

    elif stay_id == 'mock_stay_004':
        # Invasive ventilation from intime+10 h to intime+36 h
        intervals.append(SupportInterval(
            support_type=SupportType.INVASIVE_VENTILATION,
            agent_name='invasive_mechanical_ventilation',
            start_time=intime + timedelta(hours=10),
            end_time=intime + timedelta(hours=36),
        ))

    elif stay_id == 'mock_stay_005':
        # Both from admission, ongoing through entire stay
        intervals.append(SupportInterval(
            support_type=SupportType.VASOPRESSOR,
            agent_name='vasopressin',
            start_time=intime,
            end_time=intime + timedelta(hours=120),
        ))
        intervals.append(SupportInterval(
            support_type=SupportType.INVASIVE_VENTILATION,
            agent_name='invasive_mechanical_ventilation',
            start_time=intime,
            end_time=intime + timedelta(hours=120),
        ))

    elif stay_id == 'mock_stay_006':
        # Non-invasive ventilation only — does NOT qualify
        intervals.append(SupportInterval(
            support_type=SupportType.INVASIVE_VENTILATION,
            agent_name='non_invasive_ventilation',
            start_time=intime + timedelta(hours=3),
            end_time=intime + timedelta(hours=24),
        ))

    return intervals


def generate_synthetic_csvs() -> None:
    """Write synthetic_stays.csv and synthetic_icu_events.csv to DATA_DIR."""
    os.makedirs(DATA_DIR, exist_ok=True)

    stays_df = get_mock_stays()
    stays_path = os.path.join(DATA_DIR, 'synthetic_stays.csv')
    stays_df.to_csv(stays_path, index=False)
    logger.info("Saved %d mock stays to %s", len(stays_df), stays_path)

    all_events = []
    for sid in MOCK_STAYS:
        all_events.append(get_mock_events(sid))

    if all_events:
        combined = pd.concat(all_events, ignore_index=True)
        events_path = os.path.join(DATA_DIR, 'synthetic_icu_events.csv')
        combined.to_csv(events_path, index=False)
        logger.info("Saved %d mock events to %s", len(combined), events_path)
