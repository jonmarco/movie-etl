import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Optional


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
