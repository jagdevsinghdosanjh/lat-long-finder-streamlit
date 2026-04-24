import base64
import streamlit as st
import json

def get_geolocation():
    """
    Modern geolocation using a hidden HTML input field.
    Works in Streamlit Cloud + Local + all browsers.
    """

    # Hidden input field for receiving JSON
    geo_input = st.text_input("geo_data_input", value="", key="geo_data_input", label_visibility="collapsed")

    # If JS wrote data into the hidden input, parse it
    if geo_input:
        try:
            return json.loads(geo_input)
        except:
            return None

    # HTML + JS that writes geolocation JSON into the hidden input
    html = """
    <html>
    <body>
    <input type="text" id="geo_data_input" style="display:none;" />

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
                document.getElementById("geo_data_input").value = JSON.stringify(data);
                document.getElementById("geo_data_input").dispatchEvent(new Event("input"));
            },
            (err) => {
                const data = {permission: "denied"};
                document.getElementById("geo_data_input").value = JSON.stringify(data);
                document.getElementById("geo_data_input").dispatchEvent(new Event("input"));
            }
        );
    }
    sendLocation();
    </script>
    </body>
    </html>
    """

    encoded = base64.b64encode(html.encode("utf-8")).decode("utf-8")
    src = f"data:text/html;base64,{encoded}"

    # Invisible iframe (height must be >= 1)
    st.iframe(src, height=1)

    return None
