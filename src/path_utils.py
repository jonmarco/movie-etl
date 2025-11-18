from pathlib import Path
from typing import Optional


def get_latest_folder(base: str, prefix: str) -> Optional[str]:
    """
    Returns the latest folder name in `base` whose name starts with `prefix`.
    Example: prefix='year=' -> returns 'year=2025'
    """
    p = Path(base)
    if not p.exists():
        return None
    candidates = [d.name for d in p.iterdir() if d.is_dir() and d.name.startswith(prefix)]
    if not candidates:
        return None
    # sort by numeric part if possible
    def key_fn(name: str) -> int:
        try:
            return int(name.split("=", 1)[1])
        except Exception:
            return -1
    return sorted(candidates, key=key_fn)[-1]


def get_last_file_path(provider_path: str) -> Optional[str]:
    """
    Returns relative path: 'year=YYYY/month=MM/day=DD' for the latest partition.
    """
    provider = Path(provider_path)
    if not provider.exists():
        return None

    year_folder = get_latest_folder(str(provider), "year=")
    if not year_folder:
        return None
    year_path = provider / year_folder

    month_folder = get_latest_folder(str(year_path), "month=")
    if not month_folder:
        return None
    month_path = year_path / month_folder

    day_folder = get_latest_folder(str(month_path), "day=")
    if not day_folder:
        return None

    return (Path(year_folder) / month_folder / day_folder).as_posix()


def get_current_date_path() -> str:
    """
    Returns 'year=YYYY/month=MM/day=DD' for today (local time).
    """
    from datetime import datetime
    now = datetime.now()
    return f"year={now.year}/month={now:%m}/day={now:%d}"
