import os
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Iterable
import pandas as pd
import yaml


def load_config(path: Optional[str] = None) -> Dict:
    """
    Load YAML config. If path is None, tries CONFIG_PATH env or 'config.yaml'.
    """
    cfg_path = path or os.environ.get("CONFIG_PATH", "config.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_files_from_dir(directory: str, extension: Optional[str] = None) -> List[pd.DataFrame]:
    """
    Read CSV/JSON/Parquet files from a directory and return a list of DataFrames.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory {directory} does not exist.")

    if extension is None:
        exts = ["csv", "json", "parquet"]
    else:
        exts = [extension.lower()]

    supported = {"csv", "json", "parquet"}
    for ext in exts:
        if ext not in supported:
            raise ValueError(f"Unsupported extension: {ext}. Supported: {sorted(supported)}")

    dfs: List[pd.DataFrame] = []
    for ext in exts:
        for fpath in sorted(Path(directory).glob(f"*.{ext}")):
            if ext == "csv":
                df = pd.read_csv(fpath)
            elif ext == "json":
                df = pd.read_json(fpath)
            elif ext == "parquet":
                df = pd.read_parquet(fpath)
            else:
                continue

            df.columns = df.columns.astype(str).str.strip()
            df.attrs["source_file"] = str(fpath)
            dfs.append(df)

    if not dfs:
        raise FileNotFoundError(f"No files with extensions {exts} found in {directory}")
    return dfs


def read_data_from_bronze_dir(
    directory: str,
    extension: Optional[str],
    merge_keys: Optional[List[str]] = None,
    rename_by_filename: Optional[List[Dict]] = None,
) -> pd.DataFrame:
    """
    Reads, renames, and merges data from a Bronze directory.

    This function is a high-level wrapper that:
      1. Reads all data files from the directory.
      2. Applies file-level renaming rules (if provided).
      3. Merges and groups the resulting DataFrames into one.

    Parameters
    ----------
    directory : str
        Path to the directory containing data files.
    extension : str
        File extension to load ("csv", "json"), or None to load both.
    merge_keys : list, optional
        Columns to group by after merging the data. If provided,
        the function returns the first record of each group.
    rename_by_filename : list, optional
        A list of rename rules applied based on the filename.

    Returns
    -------
    pandas.DataFrame
        A consolidated DataFrame after reading, renaming, and merging.
    """
    dfs = read_files_from_dir(directory, extension)
    dfs = apply_file_level_renames(dfs, rename_by_filename)
    df_all = merge_dataframes(dfs, merge_keys)
    return df_all



def apply_file_level_renames(
    dfs: List[pd.DataFrame],
    rename_by_filename: Optional[List[Dict]] = None,
) -> List[pd.DataFrame]:
    """
    Apply column renames to each DataFrame based on filename glob patterns.
    """
    if not rename_by_filename:
        return dfs

    out: List[pd.DataFrame] = []
    for df in dfs:
        fpath = df.attrs.get("source_file", "")
        for rule in rename_by_filename:
            pattern = rule.get("match_glob")
            rename_map = rule.get("rename", {})
            if not pattern or not rename_map:
                continue
            if fnmatch.fnmatch(fpath, pattern) or fnmatch.fnmatch(os.path.basename(fpath), pattern):
                df = df.rename(columns=rename_map)
        out.append(df)
    return out


def write_dataset(
    df: pd.DataFrame,
    config: Dict,
    layer: str,
    provider: Optional[str] = None,
    *,
    fmt: str = "parquet",
    filename: str = "data_clean",
    relative_partition_path: Optional[str] = None,
    overwrite: bool = True,
) -> str:
    """
    Write a DataFrame to a configured layer ('silver', 'gold', 'hist') in CSV or Parquet.
    If `relative_partition_path` is given (e.g., 'year=2025/month=11/day=17'), it is used.
    """
    layer_key = f"{layer}_path"
    if layer_key not in config:
        raise KeyError(f"config must include '{layer_key}'")

    fmt = (fmt or "").lower()
    if fmt not in {"parquet", "csv"}:
        raise ValueError(f"Unsupported fmt='{fmt}'. Use 'parquet' or 'csv'.")

    base_path = config[layer_key]
    parts: List[str] = [base_path]
    if provider:
        parts.append(provider)    
    if relative_partition_path:
        parts.append(relative_partition_path)


    out_dir = os.path.join(*parts)
    os.makedirs(out_dir, exist_ok=True)

    ext = ".parquet" if fmt == "parquet" else ".csv"
    out_path = os.path.join(out_dir, f"{filename}{ext}")

    if not overwrite and os.path.exists(out_path):
        raise FileExistsError(f"Output already exists: {out_path}")

    if fmt == "parquet":
        df.to_parquet(out_path, index=False)
    else:
        df.to_csv(out_path, index=False)

    return out_path


def merge_dataframes(
    dfs: List[pd.DataFrame],
    merge_keys: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Concatenates and consolidates a list of DataFrames into a single DataFrame.

    Parameters
    ----------
    dfs : list[pandas.DataFrame]
        List of DataFrames to merge.
    merge_keys : list, optional
        Columns to group by after merging the data.
        If provided, the function returns the first record of each group.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing all merged and optionally grouped data.
    """
    if not dfs:
        return pd.DataFrame()

    df_all = pd.concat(dfs, ignore_index=True, sort=False)

    if merge_keys:
        df_all = df_all.sort_values(merge_keys)
        df_all = df_all.groupby(merge_keys, as_index=False).first()

    return df_all
