import os
import time
from datetime import datetime

import pandas as pd
import pydeck as pdk
import streamlit as st
from common.geolocation import get_geolocation

location = get_geolocation()


# ---------------- CONFIG ----------------

st.set_page_config(
    page_title="Lat‑Long Finder (Cloud)",
    page_icon="📍",
    layout="wide",
)

# On Streamlit Cloud, filesystem is ephemeral but writable during a session
LOG_FILE = "access_log_cloud.csv"

TEACHER_PASSWORD = st.secrets.get("TEACHER_PASSWORD", None)


# ---------------- UTILITIES ----------------

def init_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session-{int(time.time() * 1000)}"


def load_logs() -> pd.DataFrame:
    try:
        df = pd.read_csv(LOG_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(
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
    return df


def save_log(entry: dict):
    df = load_logs()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(LOG_FILE, index=False)


def get_role() -> str:
    return st.session_state.get("role", "Student")


def set_role(role: str):
    st.session_state.role = role


def teacher_authenticated() -> bool:
    if TEACHER_PASSWORD is None:
        # If no secret set, treat as open (for quick demos)
        return True
    return st.session_state.get("teacher_authed", False)


def teacher_login_ui():
    st.subheader("Teacher login (Cloud)")
    if TEACHER_PASSWORD is None:
        st.info("No TEACHER_PASSWORD secret configured. Teacher mode is open for this deployment.")
        st.session_state.teacher_authed = True
        return

    pwd = st.text_input("Enter teacher password", type="password")
    if st.button("Login"):
        if pwd == TEACHER_PASSWORD:
            st.session_state.teacher_authed = True
            st.success("Teacher authenticated.")
        else:
            st.error("Incorrect password.")


# ---------------- APP LAYOUT ----------------

init_session()

st.title("📍 Lat‑Long Finder for Classrooms (Cloud)")
st.caption("Streamlit Cloud app for geolocation, logging, and analytics.")

with st.sidebar:
    st.header("Mode")
    mode = st.radio("Select mode", ["Student", "Teacher"], index=0)
    set_role(mode)

    st.markdown("---")
    st.subheader("About")
    st.markdown(
        """
        - **Student mode**: capture location + class info  
        - **Teacher mode**: view logs, maps, and analytics  
        - Data is stored in `access_log_cloud.csv` (resets on redeploy).  
        """
    )
    st.markdown("**Privacy note**")
    st.markdown(
        """
        - Location is used only for demonstration / teaching.  
        - No third‑party tracking is added.  
        """
    )

role = get_role()

# ---------------- STUDENT MODE ----------------

if role == "Student":
    st.markdown("## 🧑‍🎓 Student mode")

    st.markdown("### 1️⃣ Enter your class details")

    col1, col2, col3 = st.columns(3)
    with col1:
        school = st.text_input("School name", placeholder="e.g. XYZ Public School")
    with col2:
        class_name = st.text_input("Class", placeholder="e.g. 10")
    with col3:
        section = st.text_input("Section", placeholder="e.g. A")

    col4, col5 = st.columns(2)
    with col4:
        student_id = st.text_input("Roll no. / Student ID", placeholder="e.g. 23")
    with col5:
        ip_label = st.text_input("Network / IP label (optional)", placeholder="e.g. Lab‑PC‑01")

    st.markdown("### 2️⃣ Capture your location")
    st.write("Click below and allow location access in your browser when prompted.")

    location = geolocation(key="student_geolocation_cloud")

    if location:
        st.success("Location data received from browser.")
    else:
        st.info("Waiting for location permission…")

    platform = st.text_input("Device / Platform (optional)", placeholder="e.g. Android / Windows / iOS")
    user_agent = st.text_input("Browser / Device info (optional)", placeholder="e.g. Chrome on Windows")

    if location:
        lat = location.get("latitude")
        lon = location.get("longitude")
        accuracy = location.get("accuracy", None)
        permission = "granted"
    else:
        lat = lon = accuracy = None
        permission = "pending"

    st.markdown("### 3️⃣ Review your data")

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Latitude", f"{lat:.6f}" if lat else "—")
        st.metric("Longitude", f"{lon:.6f}" if lon else "—")
    with col_b:
        st.metric("Accuracy (m)", f"{accuracy:.1f}" if accuracy else "—")
        st.metric("Permission", permission)

    st.markdown("### 4️⃣ Submit to teacher log")

    can_log = all([school, class_name, section, student_id, lat, lon])

    if st.button("Submit my location", type="primary", disabled=not can_log):
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
        st.success("Your location has been submitted to the teacher log ✅")

    st.markdown("### 5️⃣ Your location on the map")
    if lat and lon:
        map_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
        st.pydeck_chart(
            pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=pdk.ViewState(
                    latitude=lat,
                    longitude=lon,
                    zoom=14,
                    pitch=45,
                ),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=map_df,
                        get_position="[lon, lat]",
                        get_color="[0, 128, 255, 200]",
                        get_radius=30,
                    )
                ],
            )
        )
    else:
        st.info("Map will appear here after your location is captured.")

# ---------------- TEACHER MODE ----------------

else:
    st.markdown("## 🧑‍🏫 Teacher mode (Cloud)")

    if not teacher_authenticated():
        teacher_login_ui()
    else:
        logs = load_logs()

        if logs.empty:
            st.info("No logs yet. Ask students to submit their locations in Student mode.")
        else:
            st.markdown("### 1️⃣ Filters")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                school_filter = st.selectbox(
                    "School",
                    options=["All"] + sorted(logs["school"].dropna().unique().tolist()),
                    index=0,
                )
            with col2:
                class_filter = st.selectbox(
                    "Class",
                    options=["All"] + sorted(logs["class_name"].dropna().unique().tolist()),
                    index=0,
                )
            with col3:
                section_filter = st.selectbox(
                    "Section",
                    options=["All"] + sorted(logs["section"].dropna().unique().tolist()),
                    index=0,
                )
            with col4:
                role_filter = st.selectbox(
                    "Role",
                    options=["All"] + sorted(logs["role"].dropna().unique().tolist()),
                    index=0,
                )

            filtered = logs.copy()
            if school_filter != "All":
                filtered = filtered[filtered["school"] == school_filter]
            if class_filter != "All":
                filtered = filtered[filtered["class_name"] == class_filter]
            if section_filter != "All":
                filtered = filtered[filtered["section"] == section_filter]
            if role_filter != "All":
                filtered = filtered[filtered["role"] == role_filter]

            st.markdown("### 2️⃣ Summary")

            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Total entries", len(filtered))
            col_b.metric("Unique students", filtered["student_id"].nunique())
            col_c.metric("Classes", filtered["class_name"].nunique())
            col_d.metric("Schools", filtered["school"].nunique())

            st.markdown("### 3️⃣ Map of all logged points")

            if not filtered["latitude"].isna().all():
                map_df = (
                    filtered[["latitude", "longitude", "school", "class_name", "section", "student_id"]]
                    .dropna()
                    .rename(columns={"latitude": "lat", "longitude": "lon"})
                )

                tooltip_text = (
                    map_df["school"].fillna("Unknown")
                    + " | Class "
                    + map_df["class_name"].fillna("?")
                    + "-"
                    + map_df["section"].fillna("?")
                    + " | Roll "
                    + map_df["student_id"].fillna("?")
                )
                map_df["tooltip"] = tooltip_text

                st.pydeck_chart(
                    pdk.Deck(
                        map_style="mapbox://styles/mapbox/light-v9",
                        initial_view_state=pdk.ViewState(
                            latitude=map_df["lat"].mean(),
                            longitude=map_df["lon"].mean(),
                            zoom=11,
                            pitch=45,
                        ),
                        layers=[
                            pdk.Layer(
                                "ScatterplotLayer",
                                data=map_df,
                                get_position="[lon, lat]",
                                get_color="[255, 0, 0, 180]",
                                get_radius=40,
                                pickable=True,
                            )
                        ],
                        tooltip={"text": "{tooltip}"},
                    )
                )
            else:
                st.info("No valid coordinates in filtered logs.")

            st.markdown("### 4️⃣ Class / section distribution")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Entries per class**")
                class_counts = (
                    filtered["class_name"].fillna("Unknown").value_counts().sort_index()
                )
                st.bar_chart(class_counts)
            with col2:
                st.markdown("**Entries per section**")
                section_counts = (
                    filtered["section"].fillna("Unknown").value_counts().sort_index()
                )
                st.bar_chart(section_counts)

            st.markdown("### 5️⃣ Raw logs")

            with st.expander("Show logs table"):
                st.dataframe(
                    filtered.sort_values("timestamp", ascending=False),
                    use_container_width=True,
                )

            st.markdown("### 6️⃣ Download logs")

            csv_bytes = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download filtered logs as CSV",
                data=csv_bytes,
                file_name="lat_long_logs_cloud_filtered.csv",
                mime="text/csv",
            )
