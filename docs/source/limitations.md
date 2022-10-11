# Limitations & Future Work

* The performance of the MatPlotLib-based front-end is poor for high-resolution plots. 
  Future work would involve re-implementing the front-end in a more modern library like Plotly.
* The code loads all the data provided into memory at launch. This limits its scalability.
  Future work would involve re-saving provided data as `parquet` or other time-indexable files for partial loads
  using the Dask and XArray libraries.
* Add configurations that load data directly from catalogues.