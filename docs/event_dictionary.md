# Event Dictionary

> **WARNING:** The data and logic described in this system are for **development and mock data only**. All data is synthetic. This is **NOT** a clinical tool and does **NOT** use real MIMIC-IV data.

## Overview
This document defines the events and states used for determining labels for predictive models, specifically focusing on the `organ_support_initiation_24h` endpoint.

## Endpoint Definition
**Endpoint**: `organ_support_initiation_24h`
**Definition**: The probability that a patient will initiate either new vasopressor support or new invasive mechanical ventilation support within the next 24 hours (t, t+24h], given they are not currently receiving that specific support at time `t`.

## Vasopressor Definition
- **Qualifying Agents**: Norepinephrine, Epinephrine, Vasopressin, Dopamine, Phenylephrine.
- **Mock Status**: Currently, mock data randomly assigns vasopressor events using standardized medication administration codes.

## Ventilation Definition
- **Invasive Mechanical Ventilation (IMV)**: Qualifies as organ support. Endotracheal tube or tracheostomy.
- **Non-Invasive Ventilation (NIV) & HFNC**: Do NOT qualify as invasive support.

## State Definitions
- **ON**: The patient is actively receiving the therapy at time `t`.
- **OFF**: The patient is not receiving the therapy at time `t`.

## Initiation Rule
An initiation event is triggered if the patient transitions from **OFF** at time `t` to **ON** at any time within the half-open interval `(t, t+24h]`.

## Censoring Rules
Data is censored (excluded from positive/negative class assignment) if follow-up is incomplete and no initiation event was observed before the stay ended.
1. **Discharge before t+24h**: Stay ends without an event before the 24h window closes.
2. **Death before t+24h**: Patient expires without an event before the 24h window closes.
3. **Data truncation**: The dataset ends before `t+24h` without an event.
4. **Already ON**: If the patient is already **ON** a specific support at time `t`, they cannot "initiate" it, thus they are censored for that specific support's initiation endpoint.

## Event-Time Policy
All history is strictly truncated at `event_time <= prediction_time`. No events occurring after `prediction_time` can be used to construct features.

## Missing Data Policy
Missing values are handled by the feature builder (e.g., carrying forward the last known value). If no prior value exists, a clinical default or population median may be imputed (details pending real feature builder implementation).

## Freeze Discipline
1. **No future data**: Features must only use data available up to `t`.
2. **Timezone awareness**: All timestamps must be in UTC.
3. **Immutable history**: Past events cannot be altered after the fact.
4. **Deterministic processing**: The same history must always yield the same features.

## Known Limitations
- Synthetically generated mock data does not reflect clinical reality.
- Simplified ventilation categorizations.

## Provenance
This dictionary is derived from standard critical care consensus definitions adapted for this synthetic retrospective study.

## MIMIC-IV Integration TODOs
- [ ] Map MIMIC-IV `itemid`s to the qualifying vasopressor agents.
- [ ] Implement MIMIC-IV ventilation status logic distinguishing IMV from NIV/HFNC.
- [ ] Develop SQL extraction scripts adhering to these definitions.
