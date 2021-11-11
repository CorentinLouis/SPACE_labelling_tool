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
    "time": "Column name, e.g. 't'",
    "frequency": "Column name, e.g. 'f'",
    "flux_density": "Column name, e.g. 's'",
    "power": "Column name, e.g. 'p'",
    "degree_of_polarisation": "Column name, e.g. 'v'"
  },
  "units": {
    "time": "Time units, e.g. 'Days'",
    "frequency": "Frequency units, e.g. 'kHz'",
    "flux_density": "Flux density units, e.g. 'Wm^{-2}Hz^{-1}'",
    "power": "Power units, e.g. 'W/sr'",
    "degree_of_polarisation": "Degree of polarisation units (probably just blank e.g. '')"
  },
  "years": [
    "Integer, year the spacecraft began taking data, e.g. 2004", 
    "Integer, year the spacecraft stopped recording data, e.g. 2017"
  ]
}
```

## Mandatory Entries

A configuration file **must** contain an `observer`, `names` for `time`, `frequency` and `flux_density`, 
units for `frequency` and the `years` of operation. The observer name and units are needed for TFCat output format, 
whilst the operational years are used for validating calls to the script.

### Polarisation

The `power` and `degree_of_polarisation` entries are needed for data files that contain polarisation data. 
A configuration file can be valid if it *over*-specifies a file (e.g. providing polarisation information for a dataset
that does not contain polarisation data) but cannot be valid if it *under*-specifies a file. 
If a file contains polarisation data, even if you are not interested in it you must still have a configuration that
describes all of the columns within that file to load it.

### Optional Units

Most of the units entries are optional, but exist for future-proofing. 
Plots can, in future, automatically title their axes based off of the units provided.
By recording units for time, it is possible to accommodate later datasets with time columns 