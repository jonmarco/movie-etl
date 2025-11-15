import os
import pytest
import pandas as pd
from src.utils import (
    get_latest_folder,
    get_last_file_path
)

class TestUtils:

    def test_get_latest_folder(self, tmp_path):
        d1 = tmp_path / "year=2022"
        d2 = tmp_path / "year=2023"
        d1.mkdir()
        d2.mkdir()

        result = get_latest_folder(str(tmp_path), "year=")
        assert result == "year=2023"

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        assert get_latest_folder(str(empty_dir), "year=") is None

    def test_get_last_file_path(self, tmp_path):
        y = tmp_path / "year=2023"
        m = y / "month=05"
        d = m / "day=10"
        d.mkdir(parents=True)

        last_path = get_last_file_path(str(tmp_path))
        assert last_path.endswith("year=2023/month=05/day=10")
        assert "/" in last_path  