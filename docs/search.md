# Exploration
Using the `/search` endpoint, you can execute a variety of searches across the MINT Model and Data Catalogs. These Catalogs are integrated via this search API to provide a high-level interface for queries. 

> Note that these queries will only return models and datasets registered to the Model Service API namespace, not the broader MINT namespace.

## Contents

- [Geo Query](#geo-query)
- [Text Query](#text-query)
- [Time Query](#time-query)

### Geo Query

A geospatial bounding box search parameter is 4-elements in the WGS84 coordinate system: `[xmin, ymin, xmax, ymax]`. `x` is longitude, `y` is latitude. 

```
{
   "query_type":"geo",
   "result_type":"datasets",
   "xmin": 33.9605286,
   "xmax": 33.9895077,
   "ymin": -118.4253354,
   "ymax": -118.4093589
}
```

### Text Query

You may search for either standard names that match your text query, or basic keyword searches across model and dataset descriptions.

```
{
   "query_type":"text",
   "result_type":"datasets",
   "term": "Country Name",
   "type": "standard name"
}
```

```
{
   "query_type":"text",
   "result_type":"models",
   "term": "food",
   "type": "keyword"
}
```

### Time Query

Time should be provided in `YYYY-MM-DDTHH:MM:SS` format.

```
{
   "query_type":"time",
   "result_type":"models",
   "start_time": "1960-01-01T00:00:00",
   "end_time": "2019-01-01T23:59:59"
}
```