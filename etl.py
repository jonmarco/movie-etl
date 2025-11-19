# src/etl.py
import logging
import argparse
from src.data_utils import load_config, write_dataset
from src.extract import Extract
from src.transform import Transform
from src.load import Load


def main():
    parser = argparse.ArgumentParser(description="Movie ETL Pipeline")
    parser.add_argument(
        "--bronze_to_silver",
        action="store_true",
        help="Run Extract + Transform stages only (Bronze -> Silver).",
    )
    parser.add_argument(
        "--silver_to_gold",
        action="store_true",
        help="Run Load stage only (Silver -> Gold, including Hist).",
    )
    parser.add_argument(
        "--filename",
        default="cleaned_data",
        help="Base filename for Silver/Gold writes (default: cleaned_data).",
    )
    parser.add_argument(
        "--loglevel",
        default="INFO",
        help="Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO).",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.loglevel.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = load_config()
    transformer = Transform(config)
    loader = Load(config)

    bronze_to_silver_only = args.bronze_to_silver and not args.silver_to_gold
    silver_to_gold_only = args.silver_to_gold and not args.bronze_to_silver
    full_pipeline = not args.bronze_to_silver and not args.silver_to_gold

    if bronze_to_silver_only or full_pipeline:
        logging.info("[ETL] Starting Bronze -> Silver stage...")
        extracted = Extract(config).extract_latest_data_all_providers()
        written = transformer.transform_and_write_to_silver(extracted, filename=args.filename)
        logging.info(f"[ETL] Bronze -> Silver completed. Written: {written}")
    else:
        logging.info("[ETL] Skipping Bronze -> Silver stage.")

    if silver_to_gold_only or full_pipeline:
        logging.info("[ETL] Starting Silver -> Gold stage...")

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
            filename=config.get("gold_filename", args.filename),
            relative_partition_path=None,
        )
        logging.info(f"[gold] Written to {out}")
    else:
        logging.info("[ETL] Skipping Silver -> Gold stage.")

    logging.info("[ETL] Pipeline finished successfully.")


if __name__ == "__main__":
    main()
