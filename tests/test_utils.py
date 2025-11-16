import os
import json
import pytest
import pandas as pd
from src.utils import (
    get_latest_folder,
    get_last_file_path,
    read_csv_from_dir,
    read_json_from_dir,
    read_data_from_dir
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

    def test_read_data_from_dir_csv_only(self, tmp_path):
        # Create CSV file
        f1 = tmp_path / "provider1_movie_data1.csv"
        f1.write_text(
            "movie_title,release_year,critic_score_percentage\n"
            "Inception,2010,87\n"
            "The Dark Knight,2008,94"
        )

        df = read_data_from_dir(str(tmp_path), extension="csv")

        assert len(df) == 2
        assert list(df.columns) == ["movie_title", "release_year", "critic_score_percentage"]


    def test_read_data_from_dir_json_only(self, tmp_path):
        # Create JSON file
        f1 = tmp_path / "provider2_movie_data1.json"
        f1.write_text(json.dumps([
            {"title": "Inception", "year": "2010", "audience_average_score": 9.1},
            {"title": "The Dark Knight", "year": "2008", "audience_average_score": 9.4}
        ]))

        df = read_data_from_dir(str(tmp_path), extension="json")

        assert len(df) == 2
        assert list(df.columns) == ["title", "year", "audience_average_score"]


    def test_read_data_from_dir_merge_two_csv(self, tmp_path):
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

        df = read_data_from_dir(
            str(tmp_path),
            extension="csv",
            merge_keys=["movie_title", "release_year"]
        )

        assert len(df) == 2
        assert set(df["movie_title"]) == {"Inception", "The Dark Knight"}

        inc_row = df[df["movie_title"] == "Inception"].iloc[0]
        assert inc_row["critic_score_percentage"] == 87
        assert inc_row["total_audience_ratings"] == 2200000

    def test_read_data_from_dir_no_valid_files(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_data_from_dir(str(tmp_path), extension="csv")
