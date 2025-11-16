import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import fnmatch


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

from pathlib import Path
from typing import Optional

def get_last_file_path(provider_path: str) -> Optional[str]:
    """
    Returns the full path of the latest directory based on a date-structured hierarchy.

    The expected directory structure is:
    provider_path/year=YYYY/month=MM/day=DD/
    The returned path is normalized to use '/' as the separator (POSIX format).

    Parameters
    ----------
    provider_path : str
        The root directory path containing year/month/day folders.

    Returns
    -------
    Optional[str]
        The full path of the latest day folder according to the directory structure.
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
    day_path = month_path / day_folder

    return day_path.as_posix()


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



def read_data_from_dir(directory: str, extension: str, merge_keys: list = None, rename_by_filename: list =None) -> pd.DataFrame:
    """
    Reads and consolidates data files from a directory, supporting both CSV and JSON formats.

    The function uses the appropriate reader based on the 'extension' argument.
    If 'extension' is 'None', both CSV and JSON files are considered.
    All loaded DataFrames are concatenated into a single DataFrame.
    Optionally, the resulting DataFrame can be grouped by one or more keys,
    returning only the first occurrence per group.

    Parameters
    ----------
    directory : str
        Path to the directory containing data files.
    extension : str
        File extension to load ("csv", "json"), or 'None' to load both.
    merge_keys : list, optional
        Columns to group by after loading the data. If provided,
        the function returns the first record of each group.
    rename_by_filename : list, optional
        A list of rename rules applied based on the filename.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing all loaded and optionally grouped data.

    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory {directory} does not exist.")

    if extension is None:
        extensions = ["csv", "json"]
    else:
        extensions = [extension.lower()]

    supported = {"csv", "json"}
    for ext in extensions:
        if ext not in supported:
            raise ValueError(f"Unsupported extension: {ext}. Supported: {sorted(supported)}")

    dfs: List[pd.DataFrame] = []
    found_any = False

    for ext in extensions:
        file_paths = sorted(Path(directory).glob(f"*.{ext}"))
        if not file_paths:
            continue

        for fpath in file_paths:
            if ext == "csv":
                df = pd.read_csv(fpath)
            elif ext == "json":
                df = pd.read_json(fpath)
            else:
                continue

            df.columns = (
                df.columns.astype(str)
                .str.strip()
            )

            if rename_by_filename:
                for rule in rename_by_filename:
                    pattern = rule.get("match_glob")
                    rename_map = rule.get("rename", {})
                    if not pattern or not rename_map:
                        continue
                    if fnmatch.fnmatch(str(fpath), pattern) or fnmatch.fnmatch(fpath.name, pattern):
                        df = df.rename(columns=rename_map)

            dfs.append(df)
            found_any = True

    if not found_any:
        raise FileNotFoundError(
            f"No files with extensions {extensions} found in {directory}"
        )

    df_all = pd.concat(dfs, ignore_index=True, sort=False)

    if merge_keys:
        df_all = df_all.sort_values(merge_keys)
        df_all = df_all.groupby(merge_keys, as_index=False).first()

    return df_all