import asyncio
import logging
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

import streamlit as st

# Project Related Imports
import json_config
from doip_engine import DoIPEngine

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

def is_connected():
    return hasattr(st.session_state, "doip_thread") and st.session_state.doip_thread.is_alive()

if st.button("Connect to DoIP Server", disabled=is_connected()):
    if is_connected():
        st.warning("Already connected to DoIP server. Please disconnect first.")
    else:
        with st.spinner("Connecting to DoIP server..."):
            engine = DoIPEngine(CONFIG_PATH)

            st.session_state.doip_thread = threading.Thread(target=asyncio.run, 
                                                            args=(engine.start_connection(),), 
                                                            daemon=True)
            st.session_state.doip_thread.start()

if is_connected():
    st.status("DoIP Client is connected and running.", state="running")
    if st.button("Disconnect from DoIP Server"):
        st.session_state.doip_thread.is_running = False

            



