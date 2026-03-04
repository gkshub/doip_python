
import json
from lib.socket import DoIPConnection


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

    async def connect_to_target(self) -> DoIPConnection:
        """Establish a connection to the DoIP target based on the configuration."""
        target_config = self.config.get("target", {})
        target_ip = target_config.get("ip_address", "127.0.0.1")