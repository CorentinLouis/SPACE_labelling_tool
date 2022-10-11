# Data Dictionary

## Inputs

### `hdf5` Files

Valid `hdf5` files for input to this code *must* contain the following columns. The names of these columns can vary,
and the code's ability to understand them is defined by the [spacecraft configurations](spacecraft_configurations.md):

* **Time (float, 1D):** The time of each observation. The time column is the index, and increases monotonically. 
  Time is recorded as Julian date.
* **Frequency (float, 1D):** The frequency of radio observation. Units will vary per spacecraft.
* **Flux (float, [Frequency, Time]):** The flux of radio emission at a given frequency and time. 

**Optional Data**

Some files will contain additional measurements as columns, for example:

* **Power (float, [Frequency, Time]):** This is the power of the radio signal measured at the given time.
* **Degree of polarization (float, [Frequency, Time]):** The degree of polarization of the radio signal at the given time.

The code can cope with any number of additional 2-d measurement columns, but they must be defined in the 
[spacecraft configurations](spacecraft_configurations.md) file.

### `cdf` File Collections

Valid `cdf` file collections are directories containing files with names in the format 
`stuff_[...]_stuff_YYYYMMDD_[???].cdf`. 
The code will read the data from all files matching apart from the date, 
and combine them into a single pre-processed data file that is saved in HDF5 format.

CDF files must contain the following variables:

* **`Epoch` (integer, 1D):** The time of each observation. This is recorded as unix epoch.
* **`Frequency` (float, 1D):** The frequency of radio observation, in any frequency unit.
* **`Data` (float, 2D):** The calibrated flux density, in  V^2 m^-2 (Freq)^-1. This is converted into per Watt.

And the following global attributes:
* **`Mission_group` (string):** The name of the mission (e.g. Juno). 

## Outputs

### TFcat `.json` Files
The code writes the selected features to file in [TFCat format](https://doi.org/10.25935/6068-8528), in the same directory as the input file
and with the same root filename (e.g. `my_data/Cassini.hdf5` will produce a `my_data/Cassini.json`).
