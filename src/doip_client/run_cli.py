import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

import asyncio

# Project Related Imports
import json_config
from doip_engine import DoIPEngine

CONFIG_PATH = json_config.get_config_path()
logger.info(f" DoIP Client Configuration Path: {CONFIG_PATH}")

async def main():
    engine = DoIPEngine(CONFIG_PATH)
    try:
        await engine.start_connection()
    except KeyboardInterrupt:
        logger.info("DoIP Engine stopped by user.")
    except Exception as e:
        logger.error(f"An error occurred while running the DoIP Engine: {e}")

if __name__ == "__main__":
    asyncio.run(main())