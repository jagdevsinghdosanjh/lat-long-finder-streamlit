import time
from datetime import datetime

import pandas as pd
import pydeck as pdk
import streamlit as st

from common.geolocation import get_geolocation

# ---------------- CONFIG ----------------

st.set_page_config(
    page_title="Lat‑Long Finder (Cloud)",
    page_icon="📍",
    layout="wide",
)

LOG_FILE = "access_log_cloud.csv"

TEACHER_PASSWORD = st.secrets.get("TEACHER_PASSWORD", None)


# ---------------- UTILITIES ----------------

def init_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session-{int(time.time() * 1000)}"


def load_logs():
    try:
        return pd.read_csv(LOG_FILE)
    except:
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


def save_log(entry):
    df = load_logs()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(LOG_FILE, index=False)


def teacher_authenticated():
    if TEACHER_PASSWORD is None:
        return True
    return st.session_state.get("teacher_authed", False)


def teacher_login_ui():
    st.subheader("Teacher Login (Cloud)")
    if TEACHER_PASSWORD is None:
        st.info("No password set in secrets. Teacher mode is open.")
        st.session_state.teacher_authed = True
        return

    pwd = st.text_input("Enter teacher password", type="password")
    if st.button("Login"):
        if pwd == TEACHER_PASSWORD:
            st.session_state.teacher_authed = True
            st.success("Authenticated.")
        else:
            st.error("Incorrect password.")


# ---------------- APP ----------------

init_session()

st.title("📍 Lat‑Long Finder for Classrooms (Cloud)")
st.caption("Streamlit Cloud app for geolocation, logging, and analytics.")

with st.sidebar:
    st.header("Mode")
    mode = st.radio("Select mode", ["Student", "Teacher"])
    st.session_state.role = mode

role = st.session_state.role

# ---------------- STUDENT MODE ----------------

if role == "Student":
    st.markdown("## 🧑‍🎓 Student Mode")

    col1, col2, col3 = st.columns(3)
    school = col1.text_input("School")
    class_name = col2.text_input("Class")
    section = col3.text_input("Section")

    col4, col5 = st.columns(2)
    student_id = col4.text_input("Roll No / Student ID")
    ip_label = col5.text_input("Network / IP Label (optional)")

    st.markdown("### Capture Location")
    location = get_geolocation()

    if location:
        st.success("Location received.")
    else:
        st.info("Waiting for location permission…")

    platform = st.text_input("Platform (optional)")
    user_agent = st.text_input("Browser / Device Info (optional)")

    if location:
        lat = location.get("latitude")
        lon = location.get("longitude")
        accuracy = location.get("accuracy")
        permission = location.get("permission")
    else:
        lat = lon = accuracy = None
        permission = "pending"

    st.markdown("### Review Data")

    colA, colB = st.columns(2)
    colA.metric("Latitude", f"{lat:.6f}" if lat else "—")
    colA.metric("Longitude", f"{lon:.6f}" if lon else "—")
    colB.metric("Accuracy", f"{accuracy:.1f}" if accuracy else "—")
    colB.metric("Permission", permission)

    can_log = all([school, class_name, section, student_id, lat, lon])

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

    if lat and lon:
        df = pd.DataFrame({"lat": [lat], "lon": [lon]})
        st.pydeck_chart(
            pdk.Deck(
                initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=14),
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
    st.markdown("## 🧑‍🏫 Teacher Mode (Cloud)")

    if not teacher_authenticated():
        teacher_login_ui()
        st.stop()

    logs = load_logs()

    if logs.empty:
        st.info("No logs yet.")
        st.stop()

    col1, col2, col3 = st.columns(3)
    school_f = col1.selectbox("School", ["All"] + logs.school.dropna().unique().tolist())
    class_f = col2.selectbox("Class", ["All"] + logs.class_name.dropna().unique().tolist())
    section_f = col3.selectbox("Section", ["All"] + logs.section.dropna().unique().tolist())

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
        "cloud_logs_filtered.csv",
        "text/csv",
    )
