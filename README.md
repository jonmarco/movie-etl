## Introduction

This project implements an ETL pipeline following a medallion architecture, consisting of three main layers:

- **Bronze** -> Raw data (as received from providers)
- **Silver** -> Cleaned and standardized data
- **Gold** -> Unified, ready-to-use dataset

Optionally, historical snapshots of the Gold layer are stored in the **'Hist'** folder.

## Installation

To install all dependencies run:
    
    pip install -r requirements.txt

## How to run the process:

Before starting the process, create the following folder structure in the project root:
data/bronze/{provider}/year=YYYY/month=MM/day=DD/

This is where the raw data files must be placed for each provider and date.

To run the complete ETL process:

    python .\etl.py

To run from only Bronze to Silver:

    python .\etl.py --bronze_to_silver

To run from silver to gold (includes moving Gold to Hist)
    
    python .\etl.py --silver_to_gold

## Running Tests

To run the complete ETL process:

    python -m pytest -v


## Config.yml

The config.yaml file defines the pipeline's structure, data formats, and transformation rules.

In the **providers** section are included:

-**subpath**: folder name under the Bronze layer

-**format**: input data format (csv, json, etc.)

-**primary_key**: unique columns identifying records

-**mapping**: field name standardization

-**file_level_renames**: (optional) rules for renaming columns based on filename patterns (in the extraction stage)


In the **cast**, the target data types for each column during the  transformation stage (bronze to silver) is defined. 


And finally, are some **settings for silver and gold layers**:

-**silver_data_format**: Output format for Silver layer files (parquet or csv).

-**overwrite_silver**: If false, skips writing when the Silver file already exists.

-**gold_data_format**: Output format for the unified Gold dataset.

-**gold_primary_key**: Columns used to merge data across providers in the Gold layer.

-**gold_filename**: Name of the output file for the Gold dataset.

-**move_to_hist**: If true, saves a dated backup of the previous Gold dataset in the Hist folder before rebuilding.
