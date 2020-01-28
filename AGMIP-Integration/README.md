# AgMIP’s Seasonal Crop Yield Emulator

Assumes that the data files are in CSVs located in `data` whose paths contain parameter information.

`AGMIP_processing.py` takes the raw files from `data` and adds columns for the appropriate parameters. Output files are stored to `data_processed` and a combined overall processed file is stored to `agmip.csv`.