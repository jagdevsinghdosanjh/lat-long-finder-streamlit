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
                const jsonData = JSON.stringify(data);
                const url = new URL(window.location.href);
                url.searchParams.set("geo_message", jsonData);
                window.location.href = url.toString();
            },
            (err) => {
                const data = {permission: "denied"};
                const jsonData = JSON.stringify(data);
                const url = new URL(window.location.href);
                url.searchParams.set("geo_message", jsonData);
                window.location.href = url.toString();
            }
        );
    };
    sendLocation();
    </script>
    """

    components.html(geo_html, height=0)

    # NEW API (Streamlit 1.30+)
    params = st.query_params

    if "geo_message" in params:
        try:
            data = json.loads(params["geo_message"])
            return data
        except:
            return None

    return None
