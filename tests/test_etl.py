# tests/test_etl_cli.py
from pathlib import Path
import os
import sys
import subprocess
import yaml
import pandas as pd


def _write_config(tmp_path: Path, content: dict) -> Path:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.dump(content), encoding="utf-8")
    return cfg


def _seed_bronze_partition(tmp_path: Path):
    p = tmp_path / "bronze" / "provider1" / "year=2025" / "month=11" / "day=17"
    p.mkdir(parents=True, exist_ok=True)
    (p / "data.csv").write_text(
        "movie_title,release_year,critic_score_percentage\n"
        "Inception,2010,87\nThe Dark Knight,2008,94\n",
        encoding="utf-8",
    )


def _seed_silver_partition(tmp_path: Path):
    p = tmp_path / "silver" / "provider1" / "year=2025" / "month=11" / "day=17"
    p.mkdir(parents=True, exist_ok=True)
    (p / "cleaned_data.csv").write_text(
        "movie_title,release_year\n"
        "Inception,2010\nThe Dark Knight,2008\n",
        encoding="utf-8",
    )


def _base_config(tmp_path: Path) -> dict:
    return {
        "bronze_path": str(tmp_path / "bronze"),
        "silver_path": str(tmp_path / "silver"),
        "gold_path": str(tmp_path / "gold"),
        "hist_path": str(tmp_path / "hist"),
        "providers": {
            "provider1": {
                "subpath": "provider1",
                "format": "csv",
                "primary_key": ["movie_title", "release_year"],
                "mapping": {
                    "movie_title": "movie_title",
                    "release_year": "release_year",
                    "critic_score_percentage": "critic_score_percentage",
                },
            }
        },
        "casts": {
            "movie_title": "string",
            "release_year": "int",
            "critic_score_percentage": "float",
        },
        "silver_data_format": "csv",
        "overwrite_silver": "true",
        "gold_data_format": "csv",
        "gold_primary_key": ["movie_title", "release_year"],
        "gold_filename": "movies",
        "move_to_hist": "true",
    }


def test_cli_default_runs_full_pipeline(tmp_path: Path):
    (tmp_path / "gold").mkdir(parents=True, exist_ok=True)
    (tmp_path / "hist").mkdir(parents=True, exist_ok=True)
    _seed_bronze_partition(tmp_path)

    pre_gold = tmp_path / "gold" / "movies.csv"
    pre_gold.write_text("movie_title,release_year\nInterstellar,2014\n", encoding="utf-8")

    cfg = _base_config(tmp_path)
    cfg_path = _write_config(tmp_path, cfg)

    env = {**os.environ, "CONFIG_PATH": str(cfg_path)}
    proc = subprocess.run(
        [sys.executable, "etl.py"], cwd=str(Path.cwd()), env=env, capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr

    silver_file = tmp_path / "silver" / "provider1" / "year=2025" / "month=11" / "day=17" / "cleaned_data.csv"
    gold_file = tmp_path / "gold" / "movies.csv"
    assert silver_file.exists()
    assert gold_file.exists()

    hist_candidates = list((tmp_path / "hist").rglob("movies.csv"))
    assert len(hist_candidates) == 1

    df_gold = pd.read_csv(gold_file)
    assert {"movie_title", "release_year"}.issubset(df_gold.columns)


def test_cli_bronze_to_silver_only(tmp_path: Path):
    (tmp_path / "gold").mkdir(parents=True, exist_ok=True)
    (tmp_path / "hist").mkdir(parents=True, exist_ok=True)
    _seed_bronze_partition(tmp_path)

    cfg = _base_config(tmp_path)
    cfg["move_to_hist"] = "true"
    cfg_path = _write_config(tmp_path, cfg)

    env = {**os.environ, "CONFIG_PATH": str(cfg_path)}
    proc = subprocess.run(
        [sys.executable, "etl.py", "--bronze_to_silver"], cwd=str(Path.cwd()), env=env, capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr

    silver_file = tmp_path / "silver" / "provider1" / "year=2025" / "month=11" / "day=17" / "cleaned_data.csv"
    gold_file = tmp_path / "gold" / "movies.csv"
    hist_candidates = list((tmp_path / "hist").rglob("movies.csv"))

    assert silver_file.exists()
    assert not gold_file.exists()
    assert len(hist_candidates) == 0


def test_cli_silver_to_gold_only(tmp_path: Path):
    (tmp_path / "gold").mkdir(parents=True, exist_ok=True)
    (tmp_path / "hist").mkdir(parents=True, exist_ok=True)
    _seed_silver_partition(tmp_path)

    cfg = _base_config(tmp_path)
    cfg["move_to_hist"] = "false"
    cfg_path = _write_config(tmp_path, cfg)

    env = {**os.environ, "CONFIG_PATH": str(cfg_path)}
    proc = subprocess.run(
        [sys.executable, "etl.py", "--silver_to_gold"], cwd=str(Path.cwd()), env=env, capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr

    gold_file = tmp_path / "gold" / "movies.csv"
    assert gold_file.exists()

    hist_candidates = list((tmp_path / "hist").rglob("movies.csv"))
    assert len(hist_candidates) == 0  

    df_gold = pd.read_csv(gold_file)
    assert set(df_gold.columns) >= {"movie_title", "release_year"}
    assert len(df_gold) >= 2
