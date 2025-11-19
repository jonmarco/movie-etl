import os
import yaml
import logging
import pandas as pd
from typing import Dict
from src.path_utils import get_last_file_path
from src.data_utils import load_config, read_data_from_bronze_dir



class Extract:
    def __init__(self, config: Dict):
        self.config = config

    def extract_latest_data_all_providers(self) -> Dict[str, pd.DataFrame]:
        """
        Extracts the latest data for each provider based on their latest folder.

        Iterates over providers in self.config, finds each provider's latest folder,
        and reads the data into a single DataFrame per provider. Providers with no
        data are skipped.

        Returns
        -------
        dict[str, pandas.DataFrame]
            Dictionary mapping provider names to consolidated DataFrames.
        """
        data: Dict[str, pd.DataFrame] = {}

        for provider, info in self.config.get("providers", {}).items():
            base_path = os.path.join(self.config["bronze_path"], info.get("subpath", ""))

            relative_last_path = get_last_file_path(base_path)
            if not relative_last_path:
                logging.info(
                    f"No latest partition found for provider '{provider}' under {base_path}. Skipping."
                )
                continue

            full_last_path = os.path.join(base_path, relative_last_path)

            try:
                provider_df = read_data_from_bronze_dir(
                    full_last_path,
                    info.get("format", ""),
                    info.get("primary_key", []),
                    info.get("file_level_renames", []),
                )
                data[provider] = provider_df                
            except FileNotFoundError as e:
                logging.warning(f"Skipping {provider}: {e}")

        return data

