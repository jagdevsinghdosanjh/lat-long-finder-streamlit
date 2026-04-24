import json
import streamlit as st
import streamlit.components.v1 as components

def get_geolocation():
    """
    Returns geolocation data from browser using JS.
    Output example:
    {
        "latitude": float,
        "longitude": float,
        "accuracy": float,
        "permission": "granted" | "denied"
    }
    """
    geo_html = """
    <script>
    const sendLocation = () => {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const data = {
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude,
                    accuracy: pos.coords.accuracy,
                    permission: "granted"
                };
                window.parent.postMessage({type: "geo_success", data: data}, "*");
            },
            (err) => {
                window.parent.postMessage({type: "geo_error", data: {permission: "denied"}}, "*");
            }
        );
    };
    sendLocation();
    </script>
    """

    components.html(geo_html, height=0)

    if "geo_data" not in st.session_state:
        st.session_state.geo_data = None

    message = st.experimental_get_query_params().get("geo_message", None)

    if message:
        try:
            st.session_state.geo_data = json.loads(message[0])
        except:
            pass

    return st.session_state.geo_data
