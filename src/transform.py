import os
import yaml
import logging
import pandas as pd
from typing import Dict
from src.utils import load_config
from src.extract import extract_latest_data_all_providers

#TODO: NEXT STEP, ADD CAST AND WRITE IN SILVER LAYER.

def apply_config_renames(provider: str, config: Dict, df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the column renames defined in the config.yaml to a provider DataFrame.

    Parameters
    ----------
    provider : str
        Name of the provider.
    config : dict
        Full configuration loaded from config.yaml.
    df : pandas.DataFrame
        DataFrame of the provider (result from the extract stage).

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns renamed according to the mapping defined in the config.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame for provider '{provider}', got {type(df)}")

    mapping = config.get("providers", {}).get(provider, {}).get("mapping", {})
    if not mapping:
        logging.info(f"[{provider}] No mapping found — returning DataFrame unchanged.")
        return df

    df.columns = (
        df.columns.astype(str)
        .str.strip()                             
    )

    valid_mapping = {k: v for k, v in mapping.items() if k in df.columns}
    missing = set(mapping.keys()) - set(df.columns)

    if missing:
        logging.warning(f"[{provider}] Columns not found for rename: {missing}")

    if valid_mapping:
        df = df.rename(columns=valid_mapping)
        logging.info(f"[{provider}] Applied rename to {len(valid_mapping)} columns.")
    else:
        logging.info(f"[{provider}] No valid columns to rename found in mapping.")

    return df


if __name__ == "__main__":
    config = load_config()
    extracted_data = extract_latest_data_all_providers(config)

    for provider, df in extracted_data.items():
        print(df.head(5))
        df_renamed = apply_config_renames(provider, config, df)
        print(df_renamed.head(5))


