import logging
import argparse
import pandas as pd

from src.utils import load_config, write_dataset
from src.extract import Extract
from src.transform import Transform
from src.load import Load

def main():
    config = load_config() 

    extractor = Extract(config)
    extracted = extractor.extract_latest_data_all_providers()

    transformer = Transform(config)
    written = transformer.transform_and_write_to_silver(extracted, filename="cleaned_data")

    loader = Load(config)
    
    move_to_hist_flag = str(config.get("move_to_hist", "false")).lower() in ["true", "1", "yes"]
    
    if move_to_hist_flag:
        logging.info("[ETL] Moving current Gold snapshot to Hist layer")
        loader.move_to_hist()
    else:
        logging.info("[ETL] move_to_hist is disabled in config")


    gold_df = loader.build_gold_from_silver()
    
    out = write_dataset(
        df=gold_df,
        config=config,
        layer="gold",
        fmt=config.get("gold_data_format", "csv"),
        filename=config.get("gold_filename", "movie_snapshot"),
        relative_partition_path=None,  
    )
    logging.info(f"[gold] Written to {out}")   




if __name__ == "__main__":
    main()    