import os
import yaml
import logging
import pandas as pd
from typing import Dict
from src.utils import get_last_file_path, read_data_from_dir, load_config

def extract_latest_data_all_providers(config: Dict) -> Dict[str, pd.DataFrame]:
    """
    Extracts the latest data for each provider based on their latest folder.

    Iterates over providers in the config, finds each provider's latest folder,
    and reads the data into a single DataFrame per provider. Providers with no 
    data are skipped.

    Parameters
    ----------
    config : dict
        Configuration dictionary with:
            - "path": root path containing provider data
            - "providers": dict mapping provider names to subpath, format, and primary_key

    Returns
    -------
    dict[str, pandas.DataFrame]
        Dictionary mapping provider names to consolidated DataFrames.
    """
    data = {}

    logging.info("Extract stage STARTED")

    for provider, info in config.get("providers", {}).items():
        logging.info(f"Reading data from {provider}")
        base_path = os.path.join(config["bronze_path"], info.get("subpath", ""))

        relative_last_path = get_last_file_path(base_path)

        if not relative_last_path:
            logging.info(f"No latest partition found for provider '{provider}' under {base_path}. Skipping.")
            continue

        full_last_path = os.path.join(base_path, relative_last_path)

        try:
            provider_df = read_data_from_dir(
                full_last_path,
                info.get("format", ""),
                info.get("primary_key", []),
                info.get("file_level_renames", []),
            )
            data[provider] = provider_df
            logging.info(f"Loaded {len(provider_df)} rows for provider {provider} from {full_last_path}")
        except FileNotFoundError as e:
            logging.warning(f"Skipping {provider}: {e}")

    return data

if __name__ == "__main__":
    config = load_config()
    extracted_data = extract_latest_data_all_providers(config)

    for provider, df in extracted_data.items():
        print(f"{provider}: {len(df)} rows")
        print(df.head(5))