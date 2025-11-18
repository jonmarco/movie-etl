import os
import logging
from typing import Dict
import pandas as pd

from pathlib import Path
from src.data_utils import write_dataset
from src.path_utils import get_last_file_path

class Transform:

    def __init__(self, config: Dict):

        self.config = config

    def apply_config_renames(self, provider: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies the column renames defined in the config.yaml to a provider DataFrame.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected a pandas DataFrame for provider '{provider}', got {type(df)}")

        mapping = self.config.get("providers", {}).get(provider, {}).get("mapping", {})
        if not mapping:
            logging.info(f"[{provider}] No mapping found — returning DataFrame unchanged.")
            return df

        df = df.copy()
        df.columns = df.columns.astype(str).str.strip()

        valid_mapping = {k: v for k, v in mapping.items() if k in df.columns}
        missing = set(mapping.keys()) - set(df.columns)

        if missing:
            logging.warning(f"[{provider}] Columns not found for rename: {missing}")

        if valid_mapping:
            df = df.rename(columns=valid_mapping)
            logging.info(f"[{provider}] Applied rename to {len(valid_mapping)} columns.")
        else:
            logging.info(f"[{provider}] No valid columns to rename found in mapping.")

        return df

    def apply_config_casts(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies column type casting to a DataFrame based on the global 'casts' section.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected a pandas DataFrame, got {type(df)}")

        casts = self.config.get("casts", {})
        if not casts:
            logging.info("No 'casts' section found in config — returning DataFrame unchanged.")
            return df

        df_casted = df.copy()
        for col, dtype in casts.items():
            if col not in df_casted.columns:
                continue
            try:
                if dtype in ("int", "int64"):
                    df_casted[col] = pd.to_numeric(df_casted[col], errors="coerce").astype("Int64")
                elif dtype in ("float", "float64"):
                    df_casted[col] = pd.to_numeric(df_casted[col], errors="coerce").astype("float64")
                elif dtype == "string":
                    df_casted[col] = df_casted[col].astype("string")
                else:
                    df_casted[col] = df_casted[col].astype(dtype)
                logging.debug(f"Casted column '{col}' to {dtype}.")
            except Exception as e:
                logging.warning(f"Failed to cast column '{col}' to {dtype}: {e}")

        return df_casted

    def _transform_provider_df(self, provider: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        Renames + casts for a provider.
        """
        df = self.apply_config_renames(provider, df)
        df = self.apply_config_casts(df)
        return df


    def transform_and_write_to_silver(
        self,
        extracted_data: Dict[str, pd.DataFrame],
        filename: str = "data_clean",
    ) -> Dict[str, str]:
        """
        Transforms extracted Bronze DataFrames (rename + cast) and writes them to the Silver layer.

        For each provider:
          - Retrieves the latest partition from Bronze (using get_last_file_path)
          - Applies renaming and type casting based on config.yaml
          - Writes the resulting DataFrame to the Silver layer, mirroring the same date partition

        Returns
        -------
        dict[str, str]
            Dictionary mapping provider names to their written Silver file paths.
        """
        written_paths: Dict[str, str] = {}
        logging.info("Silver transform stage STARTED")

        overwrite_flag = str(self.config.get("overwrite_silver", "false")).lower() in ("true", "1", "yes")


        for provider, df in extracted_data.items():
            logging.info(f"Processing provider: {provider}")

            base_path = os.path.join(self.config["bronze_path"], self.config["providers"][provider]["subpath"])
            relative_partition_path = get_last_file_path(base_path)
            if not relative_partition_path:
                logging.warning(f"No Bronze partitions found for provider '{provider}', skipping.")
                continue

            df_out = self._transform_provider_df(provider, df)

            fmt = self.config.get("silver_data_format", "csv").lower()
            ext = ".parquet" if fmt == "parquet" else ".csv"

            silver_base = Path(self.config["silver_path"])
            rel_parts = relative_partition_path.split("/")
            out_dir = silver_base.joinpath(provider,*rel_parts)
            out_dir.mkdir(parents=True, exist_ok=True)

            out_path = out_dir / f"{filename}{ext}"

            if os.path.exists(out_path) and not overwrite_flag:
¡               logging.info(f"[SKIP] Silver file already exists for provider '{provider}': {out_path}")
                written_paths[provider] = out_path
                continue

            try:
                out_path = write_dataset(
                    df=df_out,
                    config=self.config,
                    layer="silver",
                    provider=provider,
                    fmt=fmt,
                    filename=filename,
                    relative_partition_path=relative_partition_path,
                )
                written_paths[provider] = out_path
                logging.info(f"Wrote Silver data for {provider}: {out_path}")
            except Exception as e:
                logging.error(f"Failed to write Silver data for {provider}: {e}")

        logging.info("Silver transform stage COMPLETED")
        return written_paths
