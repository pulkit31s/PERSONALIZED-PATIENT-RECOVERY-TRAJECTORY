import streamlit as st
import requests
from datetime import datetime, timezone

st.set_page_config(page_title="ICU Recovery Replay", layout="wide")

st.warning("RETROSPECTIVE SEQUENTIAL REPLAY — NOT REAL-TIME CLINICAL PREDICTION", icon="⚠️")
st.title("Personalized Patient Recovery Trajectory")

# Demo mock stays
STAYS = ["mock_stay_001", "mock_stay_002", "mock_stay_003", "mock_stay_004", "mock_stay_005"]
# At least three legal replay cutoffs
CUTOFFS = [
    "2026-01-01T12:00:00Z",
    "2026-01-01T18:00:00Z",
    "2026-01-02T06:00:00Z",
]

col1, col2 = st.columns(2)
with col1:
    stay_id = st.selectbox("Select Patient Stay", STAYS)
with col2:
    cutoff_time = st.selectbox("Select Replay Cutoff", CUTOFFS)

API_URL = "http://localhost:8000/predict"

if st.button("Run Prediction"):
    payload = {
        "stay_id": stay_id,
        "prediction_time": cutoff_time,
        "include_explanations": True
    }
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            data = response.json()
            
            st.success("Prediction retrieved successfully")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.subheader("Recovery (+24h / +48h)")
                rec = data['predictions']['recovery']
                st.metric("SOFA Delta 24h", rec['delta_24h'])
                st.metric("SOFA Delta 48h", rec['delta_48h'])
                st.metric("Reconstructed SOFA 24h", rec['reconstructed_sofa_24h'])
                st.metric("Reconstructed SOFA 48h", rec['reconstructed_sofa_48h'])
                st.caption("Actual vs predicted distinction is maintained.")
            
            with col_b:
                st.subheader("Remaining ICU Time")
                icu = data['predictions']['icu_stay_time']
                st.metric("Remaining Hours", round(icu['remaining_hours'], 1))
            
            with col_c:
                st.subheader("Organ Support Risk")
                org = data['predictions']['organ_support']
                st.metric("Calibrated Probability", f"{org['calibrated_probability']:.2%}")
                st.metric("Threshold", f"{org['threshold']:.2%}")
                st.metric("Support Class", str(org['support_class']))
                
            st.subheader("Task-Specific Explanations")
            if data.get('explanations'):
                for task, exp in data['explanations'].items():
                    with st.expander(f"Task: {task} (Method: {exp['method']})"):
                        st.json(exp['items'])
                        
            st.subheader("Data Quality & Metadata")
            with st.expander("Data Quality"):
                st.json(data['data_quality'])
            with st.expander("Task Metadata"):
                st.json(data['metadata'])
                
        else:
            st.error(f"Error {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
