import os
import yaml
import logging
import pandas as pd
from typing import Dict
from src.utils import load_config
from src.extract import extract_latest_data_all_providers

#TODO: NEXT STEP, WRITE IN SILVER LAYER.

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


def apply_config_casts(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """
    Applies column type casting to a DataFrame based on the global 'casts' section
    defined in the config.yaml.

    Only casts columns that exist in the DataFrame and logs any missing ones.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to cast.
    config : dict
        The full configuration dictionary loaded from config.yaml. Must include a 'casts' section.

    Returns
    -------
    pandas.DataFrame
        The DataFrame with columns cast to the types defined in config['casts'].
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame, got {type(df)}")

    casts = config.get("casts", {})
    if not casts:
        logging.info("No 'casts' section found in config — returning DataFrame unchanged.")
        return df

    df_casted = df.copy()
    for col, dtype in casts.items():
        if col not in df_casted.columns:
            continue

        try:
            if dtype in ("int", "int64"):
                df_casted[col] = pd.to_numeric(df_casted[col], errors="coerce").astype("Int64")
            elif dtype in ("float", "float64"):
                df_casted[col] = pd.to_numeric(df_casted[col], errors="coerce").astype("float64")
            elif dtype == "string":
                df_casted[col] = df_casted[col].astype("string")
            else:
                df_casted[col] = df_casted[col].astype(dtype)
            logging.debug(f"Casted column '{col}' to {dtype}.")
        except Exception as e:
            logging.warning(f"Failed to cast column '{col}' to {dtype}: {e}")

    return df_casted



if __name__ == "__main__":
    config = load_config()
    extracted_data = extract_latest_data_all_providers(config)

    for provider, df in extracted_data.items():
        print(df.head(5))
        df_renamed = apply_config_renames(provider, config, df)
        print(df_renamed.head(5))
        df_casted = apply_config_casts(df_renamed, config)

