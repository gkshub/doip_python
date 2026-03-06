import logging
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

import os
import json
from jsonschema import validate, ValidationError

def get_config_path():
    #  Get the absolute path of the directory where app.py lives (the 'src' folder)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    #  This is the 'src' directory
    src_dir = os.path.dirname(current_dir)
    #  Go up one level to the root (doip_python)
    root_dir = os.path.dirname(src_dir)
    # 3. Join with the config folder
    config_path = os.path.join(root_dir, "config", "config_client.json")
    return config_path

# Validate the JSON data against the schema
# This function can be used in the Streamlit app before saving the configuration 
# to ensure that the JSON is valid and adheres to the expected structure.
#### TO BE IMPLEMENTED LATER ####  
def validate_config(data, schema_path): 
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    try:
        validate(instance=data, schema=schema)
        return True, "Valid"
    except ValidationError as e:
        return False, e.message

