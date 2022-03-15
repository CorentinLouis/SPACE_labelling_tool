# Data Dictionary

# Inputs

## `.hdf` Files

Valid `.hdf` files for input to this code *must* contain the following columns. The names of these columns can vary,
and the code's ability to understand them is defined by the [spacecraft configurations](spacecraft_configurations.md):

* **Time (float, 1D):** The time of each observation. The time column is the index, and increases monotonically. 
  Time is recorded as Julian date.
* **Frequency (float, 1D):** The frequency of radio observation. Units will vary per spacecraft.
* **Flux (float, [Frequency, Time]):** The flux of radio emission at a given frequency and time. 

### Optional Data

Some files will contain additional measurements as columns, for example:

* **Power (float, [Frequency, Time]):** This is the power of the radio signal measured at the given time.
* **Degree of polarization (float, [Frequency, Time]):** The degree of polarization of the radio signal at the given time.

The code can cope with any number of additional 2-d measurement columns, but they must be defined in the 
[spacecraft configurations](spacecraft_configurations.md) file.

# Outputs

## TFcat `.json` Files

The code writes the selected features to file in TFCat format, in the same directory as the input file
and with the same root filename (e.g. `my_data/Cassini.hdf5` will produce a `my_data/Cassini.json`).

