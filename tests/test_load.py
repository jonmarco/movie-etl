from pathlib import Path
import pandas as pd

from src.load import extract_latest_data_silver

class TestLoad:
    def test_extract_latest_data_silver_happy_path(self, tmp_path: Path):
        silver_root = tmp_path / "silver"
        silver_root.mkdir()

        p1_dir = silver_root / "provider1" / "year=2025" / "month=11" / "day=17"
        p2_dir = silver_root / "provider2" / "year=2025" / "month=11" / "day=17"
        p1_dir.mkdir(parents=True)
        p2_dir.mkdir(parents=True)

        (p1_dir / "p1.csv").write_text(
            "movie_title,release_year,critic_score_percentage\n"
            "Inception,2010,87\n"
            "The Dark Knight,2008,94\n",
            encoding="utf-8",
        )
        (p2_dir / "p2.csv").write_text(
            "movie_title,release_year,audience_average_score\n"
            "Inception,2010,9.0\n"
            "Interstellar,2014,8.8\n",
            encoding="utf-8",
        )

        config = {
            "silver_path": str(silver_root),
            "silver_data_format": "csv",
            "providers": {
                "provider1": {"subpath": "provider1", "format": "csv", "primary_key": ["movie_title", "release_year"]},
                "provider2": {"subpath": "provider2", "format": "csv", "primary_key": ["movie_title", "release_year"]},
            },
            "gold_primary_key": ["movie_title", "release_year"],
        }

        df = extract_latest_data_silver(config)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert {"movie_title", "release_year"}.issubset(df.columns)
        assert {"Inception", "The Dark Knight", "Interstellar"} == set(df["movie_title"].tolist())

    def test_extract_latest_data_silver_no_partitions(self, tmp_path: Path):
        silver_root = tmp_path / "silver"
        silver_root.mkdir()
        (silver_root / "provider1").mkdir()

        config = {
            "silver_path": str(silver_root),
            "silver_data_format": "csv",
            "providers": {
                "provider1": {"subpath": "provider1", "format": "csv", "primary_key": ["movie_title", "release_year"]},
            },
            "gold_primary_key": ["movie_title", "release_year"],
        }

        df = extract_latest_data_silver(config)
        assert isinstance(df, pd.DataFrame)
        assert df.empty