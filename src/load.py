import os
import logging
from typing import Dict, List, Optional
import pandas as pd

from src.data_utils import write_dataset, read_files_from_dir, merge_dataframes
from src.path_utils import get_last_file_path, get_current_date_path

class Load:

    def __init__(self, config: Dict):
        self.config = config

    def build_gold_from_silver(self) -> pd.DataFrame:
        """
        Reads the latest Silver partitions for each provider,
        concatenates all of them, and merges by the global gold_primary_key.

        Returns
        -------
        pandas.DataFrame
            Unified DataFrame across all providers based on gold_primary_key.
        """

        if "gold_primary_key" not in self.config or not self.config["gold_primary_key"]:
            raise KeyError("Config must include a non-empty 'gold_primary_key' list.")

        logging.info("Load stage STARTED (reading from SILVER)")
        df_union: List[pd.DataFrame] = []

        for provider, info in self.config.get("providers", {}).items():
            logging.info(f"[silver] Reading data from {provider}")

            base_path = os.path.join(self.config["silver_path"], info.get("subpath", ""))
            relative_last_path = get_last_file_path(base_path)
            if not relative_last_path:
                logging.info(
                    f"[silver] No latest partition found for '{provider}' under {base_path}. Skipping."
                )
                continue

            full_last_path = os.path.join(base_path, relative_last_path)

            try:
                dfs = read_files_from_dir(
                    directory=full_last_path,
                    extension=self.config.get("silver_data_format", ""),
                )
                provider_df = pd.concat(dfs, ignore_index=True, sort=False)
                df_union.append(provider_df)
                logging.info(f"[silver] Loaded {len(provider_df)} rows for {provider} from {full_last_path}")
            except FileNotFoundError as e:
                logging.warning(f"[silver] Skipping {provider}: {e}")

        gold_pk = self.config["gold_primary_key"]
        united_dataframe = merge_dataframes(df_union, merge_keys=gold_pk)
        logging.info(f"[silver] Unified dataframe built with {len(united_dataframe)} rows using PK {gold_pk}")
        return united_dataframe


    def move_to_hist(self) -> Optional[str]:
        """
        Concatenates the current Gold dataset and writes a dated snapshot to Hist.

        If no Gold files exist, logs a warning and skips the write.

        Returns
        -------
        str | None
            Full path of the written file in the Hist layer,
            or None if no Gold files were found.
        """
        gold_path = self.config["gold_path"]

        try:
            dfs = read_files_from_dir(
                directory=gold_path,
                extension=self.config.get("gold_data_format", "csv"),
            )
        except FileNotFoundError:
            logging.warning(f"[hist] No Gold files found under {gold_path}. Skipping move_to_hist.")
            return None

        if not dfs:
            logging.warning(f"[hist] No Gold data found in {gold_path}. Skipping move_to_hist.")
            return None

        gold_df = pd.concat(dfs, ignore_index=True, sort=False)
        if gold_df.empty:
            logging.warning(f"[hist] Gold DataFrame is empty. Nothing to write to Hist.")
            return None

        relative_partition_path = get_current_date_path()  
        out_path = write_dataset(
            df=gold_df,
            config=self.config,
            layer="hist",
            fmt=self.config.get("gold_data_format", "csv"),
            filename=self.config.get("gold_filename", "gold_snapshot"),
            relative_partition_path=relative_partition_path,
        )

        logging.info(f"[hist] Snapshot written to {out_path}")
        return out_path
