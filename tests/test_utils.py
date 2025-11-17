import os
import json
import pytest
import pandas as pd
import yaml
from src.utils import (
    load_config,
    get_latest_folder,
    get_last_file_path,
    read_csv_from_dir,
    read_json_from_dir,
    read_data_from_bronze_dir
)

class TestUtils:

    def test_load_config_ok(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_content = {
            "bronze_path": str(tmp_path),
            "providers": {
                "provider1": {"subpath": "provider1", "format": "csv", "primary_key": ["movie_id"]}
            }
        }
        config_file.write_text(yaml.dump(config_content))

        config = load_config(str(config_file))
        assert isinstance(config, dict)
        assert "bronze_path" in config
        assert "providers" in config
        assert "provider1" in config["providers"]

    def test_load_config_missing_file(self, tmp_path):
        missing_file = tmp_path / "no_config.yaml"
        with pytest.raises(FileNotFoundError):
            load_config(str(missing_file)) 


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


    def test_read_csv_from_dir_ok(self, tmp_path):
        f1 = tmp_path / "provider1_movie_data1.csv"
        f2 = tmp_path / "provider1_movie_data2.csv"

        f1.write_text("movie_title,release_year,critic_score_percentage\nInception,2010,87\nThe Dark Knight,2008,94")
        f2.write_text("movie_title,release_year,critic_score_percentage\nParasite,2019,99")

        df = read_csv_from_dir(str(tmp_path))

        assert len(df) == 3
        assert list(df.columns) == ["movie_title","release_year","critic_score_percentage"]

    def test_read_csv_from_dir_missing_dir(self):
        with pytest.raises(FileNotFoundError):
            read_csv_from_dir("no_such_directory")

    def test_read_csv_from_dir_no_files(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_csv_from_dir(str(tmp_path))


    def test_read_json_from_dir_ok(self, tmp_path):
        f1 = tmp_path / "provider2_movie_data1.json"

        f1.write_text(json.dumps([{"title": "Inception", "year": "2010", "audience_average_score": 9.1 }, 
            {"title": "The Dark Knight", "year": "2008", "audience_average_score": 9.4}]))        

        df = read_json_from_dir(str(tmp_path))

        assert len(df) == 2
        assert list(df.columns) == ["title","year","audience_average_score"]

    def test_read_json_from_dir_missing_dir(self):
        with pytest.raises(FileNotFoundError):
            read_json_from_dir("no_such_directory")

    def test_read_json_from_dir_no_files(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_json_from_dir(str(tmp_path))

    def test_read_data_from_bronze_dir_csv_only(self, tmp_path):
        # Create CSV file
        f1 = tmp_path / "provider1_movie_data1.csv"
        f1.write_text(
            "movie_title,release_year,critic_score_percentage\n"
            "Inception,2010,87\n"
            "The Dark Knight,2008,94"
        )

        df = read_data_from_bronze_dir(str(tmp_path), extension="csv")

        assert len(df) == 2
        assert list(df.columns) == ["movie_title", "release_year", "critic_score_percentage"]


    def test_read_data_from_bronze_dir_json_only(self, tmp_path):
        # Create JSON file
        f1 = tmp_path / "provider2_movie_data1.json"
        f1.write_text(json.dumps([
            {"title": "Inception", "year": "2010", "audience_average_score": 9.1},
            {"title": "The Dark Knight", "year": "2008", "audience_average_score": 9.4}
        ]))

        df = read_data_from_bronze_dir(str(tmp_path), extension="json")

        assert len(df) == 2
        assert list(df.columns) == ["title", "year", "audience_average_score"]


    def test_read_data_from_bronze_dir_merge_two_csv(self, tmp_path):
        f1 = tmp_path / "provider1_movie_data1.csv"
        f2 = tmp_path / "provider1_movie_data2.csv"

        f1.write_text(
            "movie_title,release_year,critic_score_percentage\n"
            "Inception,2010,87\n"
            "The Dark Knight,2008,94"
        )

        f2.write_text(
            "movie_title,release_year,total_audience_ratings,domestic_box_office_gross\n"
            "Inception,2010,2200000,533345358\n"
            "The Dark Knight,2008,2400000,535234033\n"
        )

        df = read_data_from_bronze_dir(
            str(tmp_path),
            extension="csv",
            merge_keys=["movie_title", "release_year"]
        )

        assert len(df) == 2
        assert set(df["movie_title"]) == {"Inception", "The Dark Knight"}

        inc_row = df[df["movie_title"] == "Inception"].iloc[0]
        assert inc_row["critic_score_percentage"] == 87
        assert inc_row["total_audience_ratings"] == 2200000

    def test_read_data_from_bronze_dir_no_valid_files(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_data_from_bronze_dir(str(tmp_path), extension="csv")

    def test_provider3_file_level_renames_and_merge(self, tmp_path):

        domestic_path = tmp_path / "provider3_domestic.csv"
        international_path = tmp_path / "provider3_international.csv"
        domestic_path.write_text(
            "film_name,year_of_release,box_office_gross_usd\n"
            "Inception,2010,292576195\n"
            "The Dark Knight,2008,533345358\n"
        )
        international_path.write_text(
            "film_name,year_of_release,box_office_gross_usd\n"
            "Inception,2010,535700000\n"
            "The Dark Knight,2008,469700000\n"
        )

        rename_by_filename = [
            {
                "match_glob": "**/provider3_domestic*.csv",
                "rename": {"box_office_gross_usd": "domestic_box_office_usd"},
            },
            {
                "match_glob": "**/provider3_international*.csv",
                "rename": {"box_office_gross_usd": "international_box_office_usd"},
            },
        ]

        df = read_data_from_bronze_dir(
            directory=str(tmp_path),
            extension="csv",
            merge_keys=["film_name", "year_of_release"],
            rename_by_filename=rename_by_filename,
        )

        cols = set(df.columns)

        assert "box_office_gross_usd" not in cols
        assert "box_office_gross_usd " not in cols  

        assert "domestic_box_office_usd" in cols
        assert "international_box_office_usd" in cols

        assert "film_name" in cols
        assert "year_of_release" in cols

        assert len(df) == 2

        df_sorted = df.sort_values(["film_name", "year_of_release"]).reset_index(drop=True)

        row0 = df_sorted.iloc[0]
        assert row0["film_name"] == "Inception"
        assert row0["year_of_release"] == 2010
        assert row0["domestic_box_office_usd"] == 292576195
        assert row0["international_box_office_usd"] == 535700000

        row1 = df_sorted.iloc[1]
        assert row1["film_name"] == "The Dark Knight"
        assert row1["year_of_release"] == 2008
        assert row1["domestic_box_office_usd"] == 533345358
        assert row1["international_box_office_usd"] == 469700000