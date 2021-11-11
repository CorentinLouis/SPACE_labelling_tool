# Data Dictionary

## `.sav` Files

Valid `.sav` files for input to this code *must* contain the following columns. The names of these columns can vary,
and the code's ability to understand them is defined by the [spacecraft configurations](spacecraft_configurations.md):

* **Time (float, 1D):** The time of each observation. The time column is the index, and increases monotonically. 
  Time is recorded in days relative to a 'year-of-origin', e.g. 31/12/2003 would be 365 for a file with year-of-origin 2003.
  Note, the year of origin will *not* necessarily be the start of the dataset; a dataset may have a year-of-origin that
  is years before the first measurement, e.g. a file that begins on 1/1/2003 would have a first entry of 2191 if the
  year-of-origin is 1997.
* **Frequency (float, 1D):** The frequency of radio observation. Units will vary per spacecraft.
* **Flux (float, [Frequency, Time]):** The flux of radio emission at a given frequency and time. 

### Polarisation Data

Some files will, additionally, contain two more columns:

* **Power (float, [Frequency, Time]):** This is the power of the radio signal measured at the given time.
* **Degree of Polarisation (float, [Frequency, Time]):** The degree of polarisation of the radio signal at the given time.
