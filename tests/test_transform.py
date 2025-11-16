import pandas as pd
import logging
import pytest

from src.transform import apply_config_renames 

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
