import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project Related Imports
import json
from lib.discovery import DoIPDiscovery
from lib.message import DoIPMessage
from lib.connection import DoIPConnection

class DoIPEngine:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config()
        # self.connection: Optional[DoIPConnection] = None  # Store the connection for later use

    def load_config(self) -> dict:
        """Load DoIP client configuration from JSON file."""
        with open(self.config_path, "r") as f:
            config = json.load(f)
        return config
    
    def connect(self):
        """Main method to handle the connection process."""
        logger.info("Starting DoIP Engine...")
        discovery = DoIPDiscovery(self.config)
        vehicle_ip = discovery.find_vehicle(timeout=self.config["timeouts"]["discovery_timeout_ms"] / 1000.0)
        
        if vehicle_ip:
            logger.info(f"Vehicle discovered at IP: {vehicle_ip}")
            # Here we would establish a TCP connection using DoIPConnection
            # self.connection = DoIPConnection(vehicle_ip, self.config)
            # await self.connection.establish()
        else:
            logger.warning("No vehicle discovered. Please check your network and try again.")

# later we can add option to connect to multiple vehicles based on the config, 
# for now we will just connect to the first one in the list
    async def connect_to_server(self) -> DoIPConnection:
        """Establish a connection to the DoIP server based on the configuration."""
        target_config = self.config.get("vehicles", [{}])[0] # Assuming we want to connect to the first vehicle in the list
        target_ip = target_config.get("ip_address", "127.0.0.1") 
        target_logical_address = target_config.get("target_logical_address", "0x0E00")