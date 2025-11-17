import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Union, Iterable
import yaml
import fnmatch
import logging


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


def get_latest_folder(path: str, prefix: str) -> Optional[str]:
    """
    Returns the folder name with the highest numeric suffix for a given prefix.

    Parameters
    ----------
    path : str
        The directory path where folders are located.
    prefix : str
        The prefix of the folders to search for (e.g., 'year=').

    Returns
    -------
    Optional[str]
        The name of the folder with the maximum number according to the prefix.
        Returns None if no folder with the given prefix exists.

    """
    folders = [d for d in os.listdir(path) if d.startswith(prefix)]
    if not folders:
        return None
    numbers = [int(d.split('=')[1]) for d in folders]
    max_number = max(numbers)
    return f"{prefix}{max_number:02d}"


def get_last_file_path(provider_path: str) -> Optional[str]:
    """
    Returns the relative path of the latest directory based on a date-structured hierarchy.

    The expected directory structure is:
        provider_path/year=YYYY/month=MM/day=DD/
    The returned path is the concatenation of the latest year, month, and day
    folders (e.g., "year=2025/month=11/day=17"), using POSIX separators.

    Parameters
    ----------
    provider_path : str
        The root directory path containing year/month/day folders.

    Returns
    -------
    Optional[str]
        The relative path (year=YYYY/month=MM/day=DD) of the latest batch folder.
        Returns None if any of the year, month, or day folders are missing.
    """
    provider_path = Path(provider_path)

    if not provider_path.exists():
        raise FileNotFoundError(f"The directory {provider_path} does not exist.")

    year_folder = get_latest_folder(str(provider_path), "year=")
    if not year_folder:
        return None

    year_path = provider_path / year_folder
    month_folder = get_latest_folder(str(year_path), "month=")
    if not month_folder:
        return None

    month_path = year_path / month_folder
    day_folder = get_latest_folder(str(month_path), "day=")
    if not day_folder:
        return None

    concatenated_directory = Path(year_folder) / Path(month_folder) / Path(day_folder)
    return concatenated_directory.as_posix()



def read_csv_from_dir(directory: str) -> pd.DataFrame:
    """
    Reads and concatenates all CSV files located inside a given directory.

    This function scans the provided directory, loads every file ending in
    '.csv' using 'pandas.read_csv' and returns a single concatenated
    DataFrame. If the directory does not exist or contains no CSV files,
    an exception is raised.

    Parameters
    ----------
    directory : str
        Path to the directory containing CSV files.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the concatenated contents of all CSV files
        found in the directory.

    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory {directory} does not exist.")

    csv_files = [f for f in os.listdir(directory) if f.endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {directory}")

    dfs: List[pd.DataFrame] = [pd.read_csv(os.path.join(directory, f)) for f in csv_files]
    return pd.concat(dfs, ignore_index=True)


def read_json_from_dir(directory: str) -> pd.DataFrame:
    """
    Reads and concatenates all JSON files located inside a given directory.

    The function loads each '.json' file in the directory into a DataFrame.
    The expected JSON structure is a list of objects (e.g. '[{...}, {...}]'),
    therefore 'lines=False' is used when calling 'pandas.read_json'.
    If no JSON files exist or if the directory does not exist,
    a 'FileNotFoundError' is raised.

    Parameters
    ----------
    directory : str
        Path to the directory containing JSON files.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the concatenated contents of all JSON files
        found in the directory.

    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory {directory} does not exist.")

    json_files = [f for f in os.listdir(directory) if f.endswith(".json")]
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {directory}")

    dfs: List[pd.DataFrame] = []

    for fname in json_files:
        path = os.path.join(directory, fname)
        try:
            # Current example format is [{},{}] -> lines=False
            df = pd.read_json(path, lines=False)
        except ValueError:
            raise ValueError(f"Invalid JSON file: {path}")

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def read_files_from_dir(directory: str, extension: Optional[str] = None) -> List[pd.DataFrame]:
    """
    Reads all data files from a directory, supporting parquet CSV and JSON formats.

    The function reads all files in the specified directory based on the given extension.
    If 'extension' is None, both CSV and JSON files are considered.
    Each file is read into a DataFrame, and all DataFrames are returned as a list.

    Parameters
    ----------
    directory : str
        Path to the directory containing data files.
    extension : str, optional
        File extension to load ("csv", "json"), or None to load both.

    Returns
    -------
    list[pandas.DataFrame]
        A list of DataFrames, one per file found in the directory.

    Raises
    ------
    FileNotFoundError
        If the directory does not exist or contains no files matching the extensions.
    ValueError
        If an unsupported extension is provided.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory {directory} does not exist.")

    if extension is None:
        extensions = ["csv", "json"]
    else:
        extensions = [extension.lower()]

    supported = {"csv", "json", "parquet"}
    for ext in extensions:
        if ext not in supported:
            raise ValueError(f"Unsupported extension: {ext}. Supported: {sorted(supported)}")

    dfs: List[pd.DataFrame] = []
    for ext in extensions:
        file_paths = sorted(Path(directory).glob(f"*.{ext}"))
        if not file_paths:
            continue

        for fpath in file_paths:
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
        raise FileNotFoundError(f"No files with extensions {extensions} found in {directory}")

    return dfs


def apply_file_level_renames(
    dfs: List[pd.DataFrame],
    rename_by_filename: Optional[List[Dict]] = None,
) -> List[pd.DataFrame]:
    """
    Applies renaming rules to each DataFrame based on filename patterns.

    The function iterates over each DataFrame and applies column renaming
    rules defined in the 'rename_by_filename' list, matching patterns
    against the file name or path.

    Parameters
    ----------
    dfs : list[pandas.DataFrame]
        List of DataFrames to process.
    rename_by_filename : list[dict], optional
        A list of rename rules applied based on the filename.

    Returns
    -------
    list[pandas.DataFrame]
        List of DataFrames with renamed columns where applicable.
    """
    if not rename_by_filename:
        return dfs

    renamed_dfs: List[pd.DataFrame] = []
    for df in dfs:
        fpath = df.attrs.get("source_file", "")
        for rule in rename_by_filename:
            pattern = rule.get("match_glob")
            rename_map = rule.get("rename", {})
            if not pattern or not rename_map:
                continue

            # Check if filename matches the pattern
            if fnmatch.fnmatch(fpath, pattern) or fnmatch.fnmatch(os.path.basename(fpath), pattern):
                df = df.rename(columns=rename_map)

        renamed_dfs.append(df)

    return renamed_dfs


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
    Write a DataFrame to a configured layer (e.g., silver, hist, gold), supporting
    both Parquet and CSV outputs and flexible partitioning.

    If you pass `relative_partition_path` (e.g., "year=2025/month=11/day=17"),
    that path will be used directly, if not, will directly write in base_path.

    Parameters
    ----------
    df : pandas.DataFrame
        Data to persist.
    config : dict
        Configuration file.
    layer : str
        Target layer key.
    provider : str, optional
        Optional subfolder under the partition path.
    fmt : {'parquet','csv'}, default 'parquet'
        Output file format.
    filename : str, default 'data_clean'
        Base filename (without extension).
    relative_partition_path : str, optional
        Relative partition path to reuse an existing partition.

    overwrite : bool, default True
        If False and file exists, raises FileExistsError.

    Returns
    -------
    str
        Full path of the written file.

    """
    layer_key = f"{layer}_path"
    if layer_key not in config:
        raise KeyError(f"config must include '{layer_key}'")

    fmt = fmt.lower()
    if fmt not in {"parquet", "csv"}:
        raise ValueError(f"Unsupported fmt='{fmt}'. Use 'parquet' or 'csv'.")

    base_path = config[layer_key]

    parts: Iterable[str] = [base_path]

    if provider:
        parts += [provider]

    if relative_partition_path:
        parts += [relative_partition_path]

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
