import os
import json
import pytest
import yaml
import pandas as pd
from src.extract import (
    load_config,
    extract_latest_data_all_providers
)

class TestExtract:
    def test_load_config_ok(self, tmp_path):
        # Crear un archivo YAML temporal
        config_file = tmp_path / "config.yaml"
        config_content = {
            "bronze_path": str(tmp_path),
            "providers": {
                "provider1": {"subpath": "provider1", "format": "csv", "primary_key": ["movie_id"]}
            }
        }
        config_file.write_text(yaml.dump(config_content))

        # Cargar config
        config = load_config(str(config_file))
        assert isinstance(config, dict)
        assert "bronze_path" in config
        assert "providers" in config
        assert "provider1" in config["providers"]

    def test_load_config_missing_file(self, tmp_path):
        missing_file = tmp_path / "no_config.yaml"
        with pytest.raises(FileNotFoundError):
            load_config(str(missing_file)) 

    def test_extract_latest_data_all_providers(self, tmp_path):
        provider_dir = tmp_path / "provider1" / "year=2025" / "month=11" / "day=15"
        provider_dir.mkdir(parents=True)

        csv_file = provider_dir / "movies.csv"
        csv_file.write_text(
            "movie_id,movie_title,release_year\n"
            "1,Inception,2010\n"
            "2,The Dark Knight,2008\n"
        )

        config = {
            "bronze_path": str(tmp_path),
            "providers": {
                "provider1": {"subpath": "provider1", "format": "csv", "primary_key": ["movie_id"]}
            }
        }

        data = extract_latest_data_all_providers(config)
        assert isinstance(data, dict)
        assert "provider1" in data
        df = data["provider1"]
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["movie_id", "movie_title", "release_year"]

    def test_extract_latest_data_no_latest_folder(self, tmp_path):

        (tmp_path / "provider1").mkdir()

        config = {
            "bronze_path": str(tmp_path),
            "providers": {
                "provider1": {"subpath": "provider1", "format": "csv", "primary_key": ["movie_id"]}
            }
        }
        data = extract_latest_data_all_providers(config)

        assert data == {}               