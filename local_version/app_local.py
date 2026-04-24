import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from datetime import datetime
import json

import pandas as pd
import pydeck as pdk
import streamlit as st

from common.geolocation import get_geolocation


# ---------------- CONFIG ----------------

st.set_page_config(
    page_title="Lat‑Long Finder (Local)",
    page_icon="📍",
    layout="wide",
)

LOG_FILE = os.path.join(os.path.dirname(__file__), "access_log_local.csv")
TEACHER_PASSWORD = "teacher123"  # Change this


# ---------------- UTILITIES ----------------

def init_session() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session-{int(time.time() * 1000)}"


def load_logs() -> pd.DataFrame:
    try:
        return pd.read_csv(LOG_FILE)
    except Exception:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "session_id",
                "role",
                "school",
                "class_name",
                "section",
                "student_id",
                "ip_label",
                "latitude",
                "longitude",
                "accuracy",
                "platform",
                "user_agent",
                "permission",
            ]
        )


def save_log(entry: dict) -> None:
    df = load_logs()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(LOG_FILE, index=False)


def teacher_authenticated() -> bool:
    return bool(st.session_state.get("teacher_authed", False))


def teacher_login_ui() -> None:
    st.subheader("Teacher Login (Local)")
    pwd = st.text_input("Enter teacher password", type="password")
    if st.button("Login"):
        if pwd == TEACHER_PASSWORD:
            st.session_state.teacher_authed = True
            st.success("Teacher authenticated.")
        else:
            st.error("Incorrect password.")


# ---------------- APP ----------------

init_session()

st.title("📍 Lat‑Long Finder for Classrooms (Local)")
st.caption("Local Streamlit app for geolocation, logging, and analytics.")

with st.sidebar:
    st.header("Mode")
    mode = st.radio("Select mode", ["Student", "Teacher"])
    st.session_state.role = mode

role = st.session_state.role

# ---------------- STUDENT MODE ----------------

if role == "Student":
    st.markdown("## 🧑‍🎓 Student Mode")

    st.markdown("### 1️⃣ Enter your class details")

    school_list = [
        "GHS Chananke Amritsar",
        "GHS Sohian Kalan",
        "GHS Sohian Khurd",
        "Other",
    ]

    class_list = ["6", "7", "8", "9", "10", "11", "12"]
    section_list = ["A", "B", "C", "D", "E", "F", "S"]

    col1, col2, col3 = st.columns(3)
    with col1:
        school = st.selectbox("School", school_list)
        if school == "Other":
            school = st.text_input("Enter school name")
    with col2:
        class_name = st.selectbox("Class", class_list)
    with col3:
        section = st.selectbox("Section", section_list)

    col4, col5 = st.columns(2)
    with col4:
        student_id = st.text_input("Roll No / Student ID", placeholder="e.g. 1")
    with col5:
        ip_label = st.text_input(
            "Network / IP Label (optional)",
            placeholder="e.g. Lab-PC-01",
        )

    st.markdown("### 2️⃣ Capture your location")
    st.write("Allow location access when prompted.")

    location = get_geolocation()

    if location:
        st.success("Location received.")
    else:
        st.info("Waiting for location permission…")

    platform = st.text_input("Platform (optional)", placeholder="e.g. Windows / Android")
    user_agent = st.text_input(
        "Browser / Device Info (optional)",
        placeholder="e.g. MS Edge",
    )

    if location:
        lat = location.get("latitude")
        lon = location.get("longitude")
        accuracy = location.get("accuracy")
        permission = location.get("permission")
    else:
        lat = None
        lon = None
        accuracy = None
        permission = "pending"

    st.markdown("### 3️⃣ Review your data")

    colA, colB = st.columns(2)
    colA.metric("Latitude", f"{lat:.6f}" if lat is not None else "—")
    colA.metric("Longitude", f"{lon:.6f}" if lon is not None else "—")
    colB.metric("Accuracy (m)", f"{accuracy:.1f}" if accuracy is not None else "—")
    colB.metric("Permission", permission)

    missing = []
    if not school:
        missing.append("School")
    if not class_name:
        missing.append("Class")
    if not section:
        missing.append("Section")
    if not student_id:
        missing.append("Roll No")
    if lat is None or lon is None:
        missing.append("Location")

    if missing:
        st.warning("Please fill: " + ", ".join(missing))

    can_log = len(missing) == 0

    st.markdown("### 4️⃣ Submit to teacher log")

    if st.button("Submit", disabled=not can_log):
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "session_id": st.session_state.session_id,
            "role": "Student",
            "school": school,
            "class_name": class_name,
            "section": section,
            "student_id": student_id,
            "ip_label": ip_label,
            "latitude": lat,
            "longitude": lon,
            "accuracy": accuracy,
            "platform": platform,
            "user_agent": user_agent,
            "permission": permission,
        }
        save_log(entry)
        st.success("Submitted successfully.")

    st.markdown("### 5️⃣ Map Preview")
    if lat is not None and lon is not None:
        df = pd.DataFrame({"lat": [lat], "lon": [lon]})
        st.pydeck_chart(
            pdk.Deck(
                initial_view_state=pdk.ViewState(
                    latitude=lat,
                    longitude=lon,
                    zoom=14,
                ),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=df,
                        get_position="[lon, lat]",
                        get_color="[0, 128, 255, 200]",
                        get_radius=40,
                    )
                ],
            )
        )

# ---------------- TEACHER MODE ----------------

else:
    st.markdown("## 🧑‍🏫 Teacher Mode (Local)")

    if not teacher_authenticated():
        teacher_login_ui()
        st.stop()

    logs = load_logs()

    if logs.empty:
        st.info("No logs yet.")
        st.stop()

    st.markdown("### Filters")

    col1, col2, col3 = st.columns(3)
    school_f = col1.selectbox(
        "School",
        ["All"] + logs.school.dropna().unique().tolist(),
    )
    class_f = col2.selectbox(
        "Class",
        ["All"] + logs.class_name.dropna().unique().tolist(),
    )
    section_f = col3.selectbox(
        "Section",
        ["All"] + logs.section.dropna().unique().tolist(),
    )

    filtered = logs.copy()
    if school_f != "All":
        filtered = filtered[filtered.school == school_f]
    if class_f != "All":
        filtered = filtered[filtered.class_name == class_f]
    if section_f != "All":
        filtered = filtered[filtered.section == section_f]

    st.markdown("### Summary")

    colA, colB, colC = st.columns(3)
    colA.metric("Total Entries", len(filtered))
    colB.metric("Unique Students", filtered.student_id.nunique())
    colC.metric("Classes", filtered.class_name.nunique())

    st.markdown("### Map")

    if not filtered.latitude.isna().all():
        df = filtered.rename(columns={"latitude": "lat", "longitude": "lon"})
        st.map(df[["lat", "lon"]])

    st.markdown("### Logs Table")
    st.dataframe(filtered.sort_values("timestamp", ascending=False))

    st.download_button(
        "Download CSV",
        filtered.to_csv(index=False).encode("utf-8"),
        "local_logs_filtered.csv",
        "text/csv",
    )
