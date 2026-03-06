import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project Related Imports
import json_config

CONFIG_PATH = json_config.get_config_path()
logger.info(f" DoIP Client Configuration Path: {CONFIG_PATH}")