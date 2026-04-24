import json
import streamlit as st
import streamlit.components.v1 as components


def get_geolocation():
    """
    Reliable geolocation using a tiny HTML component.
    Works in Streamlit Cloud + Local + all modern browsers.
    """

    # Hidden text input that JS will write into
    geo_json = st.text_input(
        "geo_data",
        value="",
        key="geo_data",
        label_visibility="collapsed",
    )

    # If JS wrote data, parse it
    if geo_json:
        try:
            return json.loads(geo_json)
        except Exception:
            return None

    # HTML block that triggers geolocation and writes into Streamlit input
    components.html(
        """
        <script>
        function sendLocation() {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const data = {
                        latitude: pos.coords.latitude,
                        longitude: pos.coords.longitude,
                        accuracy: pos.coords.accuracy,
                        permission: "granted"
                    };
                    const input = window.parent.document.querySelector('input[id="geo_data"]');
                    if (input) {
                        input.value = JSON.stringify(data);
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                },
                (err) => {
                    const data = { permission: "denied" };
                    const input = window.parent.document.querySelector('input[id="geo_data"]');
                    if (input) {
                        input.value = JSON.stringify(data);
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            );
        }
        sendLocation();
        </script>
        """,
        height=1,
    )

    return None
