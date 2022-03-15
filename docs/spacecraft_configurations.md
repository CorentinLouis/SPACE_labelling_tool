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
    "Power": "Column name, e.g. 'p' (optional)",
    "Degree of polarization": "Column name, e.g. 'v' (optional)"
  },
  "units": {
    "Time": "Time units, e.g. 'Days'",
    "Frequency": "Frequency units, e.g. 'kHz'",
    "Flux density": "Flux density units, e.g. 'Wm^{-2}Hz^{-1}'",
    "Power": "Power units, e.g. 'W/sr' (optional)",
    "Degree of polarization": "Degree of polarization units (probably just blank e.g. '')(optional)"
  },
  "years": [
    "Integer, year the spacecraft began taking data, e.g. 2004", 
    "Integer, year the spacecraft stopped recording data, e.g. 2017"
  ]
}
```

## Mandatory Entries

A configuration file **must** contain an `observer`, `names` and `units` for `Time`, `Frequency` and `Flux density`,
 and the `years` of operation. The observer name is needed for TFCat output format, 
whilst the operational years are used for validating calls to the script.

Each measurement requires a corresponding entry in `units`. These are displayed on the figures,
and can use LaTeX formatting like `^{2}` or `\alpha`. You do not need to wrap LaTeX text in `$` symbols. 

### Optional Entries

Optional entries can include `Power` and `Degree of polarization`, but any measurement can be
added. The key used (e.g. `Power`) will be the display name for the measurement used in the tool. 

A configuration file can be valid if it *over*-specifies a file (e.g. providing polarization information for a dataset
that does not contain polarization data) but cannot be valid if it *under*-specifies a file. 
If a file contains polarization data, even if you are not interested in it, you must still have a configuration that
describes all the columns within that file to load it.

## Creating New Configurations

To create a configuration file for a new spacecraft, copy the example above or the pre-made
[example.json](example.json) file, name it appropriately, and place it in the `config` folder.
If you have installed the labelling tool in editable mode, it should recognise the new file.
