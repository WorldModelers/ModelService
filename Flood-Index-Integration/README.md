# Setting up Flood Severity Index Model

Information for obtaining the flood files is in contained in `Flood-Files.csv`. The `flood_index_data.py` script automatically downloads these files and pushes them to S3, while creating entries for these "runs" in Redis.

You can then run `flood_index_processing.py` which converts each NetCDF flood file to a dataframe, groups it by month, and ingests it into the MaaS DB.