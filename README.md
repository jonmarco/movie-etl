## Introduction

This project implements an ETL pipeline following a medallion architecture, consisting of three main layers:

- **Bronze** -> Raw data (as received from providers)
- **Silver** -> Cleaned and standardized data
- **Gold** -> Unified, ready-to-use dataset

Optionally, historical snapshots of the Gold layer are stored in the **'Hist'** folder.

## Installation

To install all dependencies run:
    
    ```pip install -r requirements.txt```

## How to run the process:

To run the complete ETL process:

    ```python etl.py```

## Running Tests

To run the complete ETL process:

    ```python -m pytest -v```


