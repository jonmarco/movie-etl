import os
import yaml
import logging
import pandas as pd
from typing import Dict
from src.utils import load_config, get_last_file_path, write_dataset, read_files_from_dir, merge_dataframes, get_current_date_path

def extract_latest_data_silver(config: Dict) -> pd.DataFrame:
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

    logging.info("Load stage STARTED")

    df_union: List[pd.DataFrame] = []

    for provider, info in config.get("providers", {}).items():
        logging.info(f"Reading data from {provider}")
        base_path = os.path.join(config["silver_path"], info.get("subpath", ""))

        relative_last_path = get_last_file_path(base_path)

        if not relative_last_path:
            logging.info(f"No latest partition found for provider '{provider}' under {base_path}. Skipping.")
            continue

        full_last_path = os.path.join(base_path, relative_last_path)

        try:
            dfs = read_files_from_dir(
                full_last_path,
                config["silver_data_format"],                
            )
            provider_df = pd.concat(dfs, ignore_index=True, sort=False)
            df_union.append(provider_df)
            logging.info(f"Loaded {len(provider_df)} rows for provider {provider} from {full_last_path}")
        except FileNotFoundError as e:
            logging.warning(f"Skipping {provider}: {e}")

    gold_pk = config["gold_primary_key"]
    united_dataframe = merge_dataframes(df_union, merge_keys=gold_pk)
    
    return united_dataframe

def move_to_hist(config: Dict):    
    base_path = os.path.join(config["gold_path"])

    dfs = read_files_from_dir(
        config["gold_path"],
        config["gold_data_format"],                
    )

    gold_df = pd.concat(dfs, ignore_index=True, sort=False)

    relative_partition_path = get_current_date_path()

    out_path = write_dataset(
            df=gold_df,
            config=config,
            layer="hist",                
            fmt=config["gold_data_format"],
            filename=config["gold_filename"], 
            relative_partition_path=relative_partition_path               
        )

if __name__ == "__main__":
    config = load_config()
    # gold_df = extract_latest_data_silver(config)
    # print(gold_df.head(5))

    # out_path = write_dataset(
    #             df=gold_df,
    #             config=config,
    #             layer="gold",                
    #             fmt=config["gold_data_format"],
    #             filename=config["gold_filename"],                
    #         )
    move_to_hist(config)