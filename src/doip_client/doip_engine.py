import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

import asyncio

# Project Related Imports
import json
from lib.discovery import DoIPDiscovery

class DoIPEngine:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config()
        self.connection = None
        self.is_running = False

    def load_config(self) -> dict:
        """Load DoIP client configuration from JSON file."""
        with open(self.config_path, "r") as f:
            config = json.load(f)
        return config
    
    async def start_connection(self):
        """
        Handles the entire lifecycle of the DoIP connection.
        This runs for the 'duration' of the connection.
        """
        logger.info("Starting DoIP Engine...")
        try:
            discovery = DoIPDiscovery(self.config)
            # Convert timeout from milliseconds to seconds (10000ms = 10s)
            timeout_seconds = 10.0

            # Use hybrid discovery: Try announcements first, then fall back to active discovery
            vehicle_ip = discovery.find_vehicle_hybrid(
                timeout=timeout_seconds,
                try_announcements_first=True
            )

            if not vehicle_ip:
                logger.warning("No vehicle discovered. Please check your network and try again.")
                return

            logger.info(f"Vehicle discovered at IP: {vehicle_ip}")

            # Accessing the nested value: config -> doip_client -> network -> tcp_port
            tcp_port = self.config["doip_client"]["network"]["tcp_port"]

            self.connection = DoIPConnection(vehicle_ip, tcp_port)
            await self.connection.connect()

            self.is_running = True
            logger.info("DoIP Engine is now running. You can implement further communication logic here.")
            await asyncio.sleep(1)  # Keep the connection alive for the specified duration

        except Exception as e:
            logger.error(f"An error occurred in DoIP Engine: {e}")
        finally:
            if self.connection:
                self.connection.close()
            logger.info("DoIP Engine has stopped.")

    async def close_connection(self):
        """Gracefully stop the DoIP connection."""
        self.is_running = False
        if self.connection:
            self.connection.close()
            logger.info("DoIP connection closed.")

# later we can add option to connect to multiple vehicles based on the config, 
# for now we will just connect to the first one in the list
    async def connect_to_server(self) -> DoIPConnection:
        """Establish a connection to the DoIP server based on the configuration."""
        target_config = self.config.get("vehicles", [{}])[0] # Assuming we want to connect to the first vehicle in the list
        target_ip = target_config.get("ip_address", "127.0.0.1") 
        target_logical_address = target_config.get("target_logical_address", "0x0E00")