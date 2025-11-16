import pandas as pd
import logging
import pytest
import numpy as np

from src.transform import apply_config_renames, apply_config_casts

def test_apply_config_renames_basic():

    provider = "provider1"
    config = {
        "providers": {
            provider: {
                "mapping": {
                    "movie_title": "movie_title",
                    "release_year": "release_year",
                    "critic_score_percentage": "critic_score_RENAMED",  # rename to new name
                }
            }
        }
    }
    df_in = pd.DataFrame(
        {
            "movie_title": ["Inception", "The Dark Knight"],
            "release_year": [2010, 2008],
            "critic_score_percentage": [87, 94],
        }
    )

    df_out = apply_config_renames(provider, config, df_in)

    assert "movie_title" in df_out.columns
    assert "release_year" in df_out.columns
    assert "critic_score_RENAMED" in df_out.columns  
    assert "critic_score_percentage" not in df_out.columns

    assert df_out.loc[0, "critic_score_RENAMED"] == 87
    assert df_out.loc[1, "critic_score_RENAMED"] == 94


def test_apply_config_renames_strips_and_warns_missing(caplog):

    provider = "provider3"
    config = {
        "providers": {
            provider: {
                "mapping": {
                    "box_office_gross_usd": "domestic_box_office_usd",
                    "year": "release_year",
                    "nonexistent_col": "should_not_appear",
                }
            }
        }
    }

    df_in = pd.DataFrame(
        {
            "film_name": ["Inception", "The Dark Knight"],
            " year ": [2010, 2008],
            "box_office_gross_usd ": [292576195, 533345358],            
        }
    )

    df_out = apply_config_renames(provider, config, df_in)

    assert "domestic_box_office_usd" in df_out.columns
    assert "release_year" in df_out.columns
    assert "box_office_gross_usd " not in df_out.columns
    assert " year " not in df_out.columns
    assert "film_name" in df_out.columns
    assert "Columns not found for rename" in caplog.text


def test_apply_config_casts_basic_types():
    
    config = {
        "casts": {
            "movie_title": "string",
            "release_year": "int",
            "critic_score_percentage": "float",
            "total_audience_ratings": "int",
            "NOT_EXISTANT_FIELD_IN_DF": "int",
        }
    }

    df_in = pd.DataFrame(
        {
            "movie_title": ["Inception", "The Dark Knight"],
            "release_year": ["2010", "2008"],            
            "critic_score_percentage": ["87", "94.0"],   
            "total_audience_ratings": ["1500000", "2200000"],
        }
    )

    dtypes_before = df_in.dtypes.copy()

    df_out = apply_config_casts(df_in, config)

    assert str(df_out["movie_title"].dtype) == "string"
    assert str(df_out["release_year"].dtype) == "Int64"
    assert str(df_out["total_audience_ratings"].dtype) == "Int64"
    assert str(df_out["critic_score_percentage"].dtype) == "float64"

    assert df_out.loc[0, "release_year"] == 2010
    assert df_out.loc[1, "release_year"] == 2008
    assert df_out.loc[0, "critic_score_percentage"] == 87.0
    assert df_out.loc[1, "critic_score_percentage"] == 94.0
    assert df_out.loc[0, "total_audience_ratings"] == 1500000
    assert df_out.loc[1, "total_audience_ratings"] == 2200000

    assert "international_box_office_usd" not in df_out.columns
    assert all(df_in.dtypes == dtypes_before)


def test_apply_config_casts_missing_and_invalid_values():

    config = {
        "casts": {
            "movie_title": "string",
            "release_year": "int",
            "domestic_box_office_usd": "int",
            "audience_average_score": "float",
        }
    }

    df_in = pd.DataFrame(
        {
            "movie_title": ["Parasite", None],  
            "release_year": ["2019", ""],       
            "domestic_box_office_usd": ["53369749", "not_a_number"],  
            "audience_average_score": ["9.0", "bad"],                 
        }
    )

    df_out = apply_config_casts(df_in, config)

    assert str(df_out["movie_title"].dtype) == "string"
    assert str(df_out["release_year"].dtype) == "Int64"
    assert str(df_out["domestic_box_office_usd"].dtype) == "Int64"
    assert str(df_out["audience_average_score"].dtype) == "float64"

    # Then: values & coercion
    assert df_out.loc[0, "release_year"] == 2019
    assert pd.isna(df_out.loc[1, "release_year"])  # <NA>

    assert df_out.loc[0, "domestic_box_office_usd"] == 53369749
    assert pd.isna(df_out.loc[1, "domestic_box_office_usd"])  # <NA>

    assert df_out.loc[0, "audience_average_score"] == 9.0
    assert np.isnan(df_out.loc[1, "audience_average_score"])  #  NaN