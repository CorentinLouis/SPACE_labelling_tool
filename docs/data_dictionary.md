# Data Dictionary

## `.hdf` Files

Valid `.hdf` files for input to this code *must* contain the following columns. The names of these columns can vary,
and the code's ability to understand them is defined by the [spacecraft configurations](spacecraft_configurations.md):

* **Time (string, 1D):** The time of each observation. The time column is the index, and increases monotonically. 
  Time is recorded in ISO-format string date, e.g. "2004-12-31 23:59:59.999" for one millisecond from midnight, 
  New Years Eve 2004.
* **Frequency (float, 1D):** The frequency of radio observation. Units will vary per spacecraft.
* **Flux (float, [Frequency, Time]):** The flux of radio emission at a given frequency and time. 

### Polarisation Data

Some files will, additionally, contain two more columns:

* **Power (float, [Frequency, Time]):** This is the power of the radio signal measured at the given time.
* **Degree of polarization (float, [Frequency, Time]):** The degree of polarization of the radio signal at the given time.
