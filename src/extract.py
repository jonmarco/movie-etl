import os
import yaml
import pandas as pd
from typing import Dict

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config.yaml")

def load_config(config_path: str = CONFIG_FILE) -> Dict:
    """
    Loads the YAML configuration file and returns it as a dictionary.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} does not exist.")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config

if __name__ == "__main__":
    config = load_config()

    print(config)