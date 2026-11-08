"""Copyright (C) 2025 Pierre Marrec
SPDX-License-Identifier: GPL-3.0-or-later
"""

from pathlib import Path

import streamlit as st

from persistence.csv_storage import CsvStorage
from persistence.repositories import AthletesRepo, ThresholdsRepo
from utils.config import load_config
from utils.constants import DEFAULT_HR_MAX, DEFAULT_HR_REST
from utils.formatting import (
    pace_min_km_to_speed_kmh,
    set_locale,
    speed_kmh_to_pace_min_km,
)
from utils.ids import new_id
from utils.styling import apply_theme

apply_theme()
st.title("Athlete")

cfg = load_config()
set_locale("fr_FR")
storage = CsvStorage(base_dir=Path(cfg.data_dir))
ath_repo = AthletesRepo(storage)
thr_repo = ThresholdsRepo(storage)

st.subheader("Athletes")

# Load existing athletes
athletes_df = ath_repo.list()
athlete_options = []
id_by_label = {}
for _, row in athletes_df.iterrows():
    label = f"{row.get('name') or 'Unnamed'} ({row.get('athleteId')})"
    athlete_options.append(label)
    id_by_label[label] = row.get("athleteId")

selected_label = None
if athlete_options:
    selected_label = st.selectbox("Select athlete", athlete_options, index=0)
    selected_athlete_id = id_by_label.get(selected_label)
else:
    st.info("No athletes yet. Use 'Add athlete' to create one.")
    selected_athlete_id = None

# Add athlete flow (button opens a small form)
if "adding_athlete" not in st.session_state:
    st.session_state["adding_athlete"] = False

if st.button("Add athlete"):
    st.session_state["adding_athlete"] = True

if st.session_state.get("adding_athlete"):
    with st.form("add-athlete-form"):
        name = st.text_input("Athlete name", value="Runner 1")
        units = st.selectbox("Units", ["metric"], index=0)
        submitted = st.form_submit_button("Save")
        if submitted:
            aid = new_id()
            ath_repo.create(
                {
                    "athleteId": aid,
                    "coachId": "coach-1",
                    "name": name,
                    "thresholdsProfileId": "default",
                    "units": units,
                    "hrRest": DEFAULT_HR_REST,
                    "hrMax": DEFAULT_HR_MAX,
                }
            )
            st.session_state["adding_athlete"] = False
            st.success("Athlete added")

st.subheader("Thresholds (manual entries)")
if selected_athlete_id is None:
    st.warning("Select an athlete to add/view thresholds.")
else:
    athlete_record = ath_repo.get(selected_athlete_id) or {}
    with st.form("athlete-details-form"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            name_value = st.text_input("Name", value=str(athlete_record.get("name") or ""))
        with col_b:
            units_value = st.selectbox("Units", ["metric"], index=0)
        with col_c:
            hr_rest_value = st.number_input(
                "Resting HR",
                min_value=30.0,
                max_value=120.0,
                value=float(athlete_record.get("hrRest") or DEFAULT_HR_REST),
                step=1.0,
            )
        hr_max_value = st.number_input(
            "Max HR",
            min_value=60.0,
            max_value=240.0,
            value=float(athlete_record.get("hrMax") or DEFAULT_HR_MAX),
            step=1.0,
        )
        if st.form_submit_button("Save athlete info"):
            ath_repo.update(
                selected_athlete_id,
                {
                    "name": name_value,
                    "units": units_value,
                    "hrRest": hr_rest_value,
                    "hrMax": hr_max_value,
                },
            )
            st.success("Athlete information updated")

    # Show existing thresholds for the selected athlete
    thr_df = thr_repo.list(athleteId=selected_athlete_id)
    if not thr_df.empty:
        st.write("Existing thresholds (edit inline):")
        threshold_display = thr_df.copy()
        threshold_display["Allure plate min (min/km)"] = threshold_display[
            "paceFlatKmhMax"
        ].map(speed_kmh_to_pace_min_km)
        threshold_display["Allure plate max (min/km)"] = threshold_display[
            "paceFlatKmhMin"
        ].map(speed_kmh_to_pace_min_km)
        threshold_display = threshold_display.drop(
            columns=["paceFlatKmhMin", "paceFlatKmhMax"]
        )
        edited = st.data_editor(
            threshold_display,
            use_container_width=True,
            disabled=["thresholdId", "athleteId"],
            hide_index=True,
        )
        save_col, delete_col = st.columns(2)
        with save_col:
            if st.button("Save threshold edits"):
                try:
                    # Persist row-by-row based on thresholdId
                    for _, row in edited.iterrows():
                        tid = row.get("thresholdId")
                        if not tid:
                            continue
                        payload = row.to_dict()
                        pace_min = payload.pop("Allure plate min (min/km)")
                        pace_max = payload.pop("Allure plate max (min/km)")
                        payload["paceFlatKmhMin"] = pace_min_km_to_speed_kmh(pace_max)
                        payload["paceFlatKmhMax"] = pace_min_km_to_speed_kmh(pace_min)
                        thr_repo.update(str(tid), payload)
                    st.success("Threshold changes saved")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save edits: {e}")

        with delete_col:
            threshold_labels = []
            threshold_id_by_label = {}
            for _, row in thr_df.iterrows():
                threshold_id = str(row.get("thresholdId") or "")
                threshold_name = str(row.get("name") or "Unnamed threshold")
                label = f"{threshold_name} ({threshold_id})"
                threshold_labels.append(label)
                threshold_id_by_label[label] = threshold_id

            selected_threshold_label = st.selectbox(
                "Threshold to delete",
                threshold_labels,
                key="athlete_threshold_delete_select",
            )
            confirm_delete = st.checkbox(
                "Confirm threshold deletion",
                value=False,
                key="athlete_threshold_delete_confirm",
            )
            if st.button("Delete selected threshold", type="secondary"):
                if not confirm_delete:
                    st.warning("Please confirm deletion first.")
                else:
                    threshold_to_delete = threshold_id_by_label.get(selected_threshold_label)
                    if threshold_to_delete:
                        thr_repo.delete(threshold_to_delete)
                        st.rerun()
                    else:
                        st.error("Unable to determine which threshold to delete.")
    else:
        st.info("No thresholds yet for this athlete.")

    with st.form("add-threshold"):
        col1, col2 = st.columns(2)
        with col1:
            th_name = st.selectbox(
                "Name", ["Fundamental", "Threshold 60", "Threshold 30", "MVA", "Max speed"]
            )
            hr_min = st.number_input("HR min", min_value=0, max_value=250, value=0)
            hr_max = st.number_input("HR max", min_value=0, max_value=250, value=150)
        with col2:
            pace_min = st.number_input(
                "Allure plate min (min/km)",
                min_value=2.0,
                max_value=30.0,
                value=5.0,
                step=0.1,
                help="Saisir une allure décimale : 5,5 correspond à 5 min 30 s/km.",
            )
            pace_max = st.number_input(
                "Allure plate max (min/km)",
                min_value=2.0,
                max_value=30.0,
                value=7.5,
                step=0.1,
                help="Saisir une allure décimale : 7,5 correspond à 7 min 30 s/km.",
            )
            ascend_min = st.number_input(
                "Ascent rate min (m/h)", min_value=0, max_value=10000, value=0
            )
            ascend_max = st.number_input(
                "Ascent rate max (m/h)", min_value=0, max_value=10000, value=0
            )
        submitted = st.form_submit_button("Add threshold")
        if submitted:
            tid = new_id()
            thr_repo.create(
                {
                    "thresholdId": tid,
                    "athleteId": selected_athlete_id,
                    "name": th_name,
                    "hrMin": hr_min,
                    "hrMax": hr_max,
                    "paceFlatKmhMin": pace_min_km_to_speed_kmh(pace_max),
                    "paceFlatKmhMax": pace_min_km_to_speed_kmh(pace_min),
                    "ascentRateMPerHMin": ascend_min,
                    "ascentRateMPerHMax": ascend_max,
                }
            )
            st.success("Threshold added")
