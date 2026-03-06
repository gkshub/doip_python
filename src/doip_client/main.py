import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

import streamlit as st

# Project Related Imports
import json_config

CONFIG_PATH = json_config.get_config_path()
logger.info(f" DoIP Client Configuration Path: {CONFIG_PATH}")

st.title("DoIP Configuration Tool 🚗")

# SECTION 1: Configuration of DoIP Parameters
st.header("1. DoIP Parameters Configuration")
with open (CONFIG_PATH, "r") as f:
    current_config = f.read()

new_config = st.text_area("Edit DoIP Configuration (JSON Format)", value=current_config, height=500)

if st.button("Save Configuration"):
    try:
        # Validate JSON format
        import json
        json.loads(new_config)
        
        # Save the new configuration to the file
        with open(CONFIG_PATH, "w") as f:
            f.write(new_config)
        
        st.success("Configuration saved successfully!")
    except json.JSONDecodeError:
        st.error("Invalid JSON format. Please correct it and try again.")

# SECTION 2: Trigger DoIP Client Connection
st.header("2. Trigger DoIP Client Connection")
st.info("Ensure that the DoIP server is running and the configuration is correct before attempting to connect.")
if st.button("Connect to DoIP Server"):
    from doip_client.doip_engine import DoIPEngine
    with st.spinner("Connecting to DoIP server..."):
        try:
            engine = DoIPEngine(CONFIG_PATH)
            result = engine.connect()
            if result:
                st.success(f"Connected to DoIP server successfully!")
            else:
                st.error(f"Failed to connect to DoIP server. {result}")
        except Exception as e:
            st.error(f"Failed to connect to DoIP server: {e}")



