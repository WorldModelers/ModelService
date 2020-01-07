# CSIRO Model Integration

## Data preparation
The CSIRO team provided compressed run data for [APSIM long-term historical](https://cloudstor.aarnet.edu.au/plus/s/aIizgIcE8bYzoS4), [APSIM backcasting](https://cloudstor.aarnet.edu.au/plus/s/wkXBRdUBKRgoAZC0), and [G-Range backcasting](https://cloudstor.aarnet.edu.au/plus/s/sXaXF7rKk4OOkas) on 1/7/2019.

The relevant APSIM files were selected (the gridded data) and combined into single tables. These tables were stored to S3 in `world-modelers/data/CSIRO`. These files are downloaded by the processing scripts at the time each script is run.