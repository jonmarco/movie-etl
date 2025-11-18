from pathlib import Path
import pandas as pd

from src.load import extract_latest_data_silver, move_to_hist

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

    def test_move_to_hist_writes_concatenated_snapshot(self, tmp_path: Path):
        gold_root = tmp_path / "gold"
        hist_root = tmp_path / "hist"
        gold_root.mkdir()
        hist_root.mkdir()

        (gold_root / "gold_part1.csv").write_text(
            "movie_title,release_year\nInception,2010\nThe Dark Knight,2008\n",
            encoding="utf-8",
        )
        (gold_root / "gold_part2.csv").write_text(
            "movie_title,release_year\nInterstellar,2014\n",
            encoding="utf-8",
        )

        config = {
            "gold_path": str(gold_root),
            "gold_data_format": "csv",
            "gold_filename": "gold_snapshot",
            "hist_path": str(hist_root),
        }

        move_to_hist(config)

        written_files = list(hist_root.rglob("gold_snapshot.csv"))
        assert len(written_files) == 1
        out_path = written_files[0]
        assert out_path.exists()

        df = pd.read_csv(out_path)
        assert len(df) == 3
        assert {"movie_title", "release_year"}.issubset(df.columns)
        assert set(df["movie_title"].tolist()) == {"Inception", "The Dark Knight", "Interstellar"}





