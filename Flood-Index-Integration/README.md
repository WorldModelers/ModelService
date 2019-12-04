# Setting up Flood Severity Index Model

You should ensure that there is a directory called `flood_results` which contains the Flood Severity Index files. Information for obtaining these files is in `Flood-Files.csv`.

Next, you should run `flood_index_data.py` to generate the appropriate runs in Redis. You can then run `flood_index_processing.py` which converts each NetCDF flood file to a dataframe, groups it by month, and ingests it into the MaaS DB.