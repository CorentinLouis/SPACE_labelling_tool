# Spacecraft Configurations

This tool is designed to read and process output files from a range of spacecraft radio detectors, 
some of which may have already undergone post-processing. By looking at the data files, it will attempt to identify
which spacecraft they have come from using the column names.

Spacecraft configurations are declared in the [config directory](../config/). 
They are JSON-format files with following structure:

```json
{
  "observer": "Spacecraft name, e.g. 'Cassini', 'Juno'",
  "names": {
    "Time": "Column name, e.g. 't'",
    "Frequency": "Column name, e.g. 'f'",
    "Flux density": "Column name, e.g. 's'",
    "Power": "Column name, e.g. 'p'",
    "Degree of polarisation": "Column name, e.g. 'v'"
  },
  "units": {
    "Time": "Time units, e.g. 'Days'",
    "Frequency": "Frequency units, e.g. 'kHz'",
    "Flux density": "Flux density units, e.g. 'Wm^{-2}Hz^{-1}'",
    "Power": "Power units, e.g. 'W/sr'",
    "Degree of polarization": "Degree of polarisation units (probably just blank e.g. '')"
  },
  "years": [
    "Integer, year the spacecraft began taking data, e.g. 2004", 
    "Integer, year the spacecraft stopped recording data, e.g. 2017"
  ]
}
```

## Mandatory Entries

A configuration file **must** contain an `observer`, `names` for `Time`, `Frequency` and `Flux density`, 
units for `Frequency` and the `years` of operation. The observer name and units are needed for TFCat output format, 
whilst the operational years are used for validating calls to the script.

### Polarisation

The `power` and `degree_of_polarization` entries are needed for data files that contain polarization data. 
A configuration file can be valid if it *over*-specifies a file (e.g. providing polarization information for a dataset
that does not contain polarization data) but cannot be valid if it *under*-specifies a file. 
If a file contains polarization data, even if you are not interested in it, you must still have a configuration that
describes all the columns within that file to load it.

### Optional Units

Most of the units entries are optional, but if present plots will automatically title their axes based off of them.
By recording units for time, it is possible to accommodate later datasets with different time formats. 
