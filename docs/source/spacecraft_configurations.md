# Spacecraft Configurations

This tool is designed to read and process output files from a range of spacecraft radio detectors, 
some of which may have already undergone post-processing. By looking at the data files, it will attempt to identify
which spacecraft they have come from using the column names.

Configurations differ depending on the file type used. The file types, and their configurations, are: 


## HDF
Spacecraft configurations for HDF5 files are declared in the [config/hdf directory](./config/hdf5). 
They are JSON-format files with following structure:

```json

{
  "time": {
    "value": "Dataset name, e.g. 't'",
    "units": "Units LaTeX, e.g. 'Days'"
  },
  "frequency": {
    "value": "Dataset name, e.g. 'f'",
    "units": "Units LaTeX, e.g. 'kHz'"
  },
  "observer": "Observer name, e.g. 'Cassini'",
  "measurements": {
    "Display Name, e.g. 'Flux density'": {
      "value": "Dataset name, e.g. 's'",
      "units": "Units LaTeX, e.g. 'Wm^{-2}Hz^{-1}'"
    },
    "Display Name 2, e.g. 'Degree of polarisation'": {
      "value": "Dataset name, e.g. 'p'",
    }
  },
  "preprocess": {
    "frequency_resolution": "Integer, the number of bins to rescale the frequency axis along e.g. 400 (optional)",,
    "time_minimum": "Float, the number of seconds to rebin the time to (optional)"
  }
}
```

### Mandatory Entries

A configuration file **must** contain an `observer`, `time` and `frequency` entry.
The observer name is needed for TFCat output format.
`time` and `frequency` both require the name of the dataset in the file that holds their values as `value`, 
and their units as `units`. Units are displayed on the figures,
and can use LaTeX formatting like `^{2}` or `\alpha`. You do not need to wrap LaTeX text in `$` symbols. 

### Optional Entries

A file must contain one or more `measurements`, each of which has a key that is their display name,
along with a `value` entry that specifies the dataset in the file that holds their values, 
and a `units` entry (as above).


## CDF
Spacecraft configurations for HDF5 files are declared in the [config/cdf directory](../config/cdf). 
They are JSON-format files with following structure:

```json
{
  "time": ["Variable name for the time axis, e.g. Epoch"],
  "frequency": ["VVariable name for the frequency axis, e.g. Frequency"],
  "measurements": [
  {
    "Display Name": {
      "value": "Variable name for value of this measurement, e.g. Data",
      "background": "Variable name for background for this measurement, e.g. Background (optional)",
      "conversion": "Float conversion factor, e.g. 0.002654418728 to get from V^2 m^-2 Hz^-1 to W m^-2 Hz^-1 (optional)",
      "units": "Units for this value after conversion in LaTeX form, e.g. 'W m^{-2} Hz^{-1}"
    }
    }
    ],
  "preprocess": {
    "frequency_resolution": "Integer, the number of bins to rescale the frequency axis along e.g. 400 (optional)",,
    "time_minimum": "Float, the number of seconds to rebin the time to (optional)"
  },
  "other": [  {"value": "1d Variable name", 
  "time" : "Variable time"}]
}
```

### Mandatory Entries

A configuration file **must** contain entries for `time` and `frequency`, and at least one entry in `measurements`.
The name used for a measurement is what will be shown on the plot.

Each measurement requires a `value` and `units`. Units are displayed on the figures, 
and can use LaTeX formatting like `^{2}` or `\alpha`. You do not need to wrap LaTeX text in `$` symbols. 
Unfortunately, the measurement units cannot be inferred from the data file as a conversion factor may apply.

### Optional Entries

A measurement can optionally have a conversion factor and a background value. 
The background, if any, is subtracted from the value. Then the value is multiplied by the conversion factor, if any.
A variable may have a conversion factor without a background.


## Common

### Preprocessing

Some data files need modifying to plot usefully.
The `frequency_resolution` parameter is used for rescaling input files to a single logarithmic range. 
It is useful for for files with linear or mixed log-linear frequency scales, and provides the number of bins 
to rescale the frequency range for datafiles of this type to. 

The `time_minimum` parameter is used for downsampling data where the time axis is so fine it causes memory issues
or results in overly-noisy plots. The data will be downsampled to give time bins of this width, in seconds.

After preprocessing, a `.preprocessed.hdf5` file will be written out, and loaded by default
next time the same file is opened (to avoid having to rerun the preprocessing each time).


## Creating New Configurations

To create a configuration file for a new spacecraft or variety of file, copy the relevant example above or the pre-made
[example.json](example.json) file from the appropriate directory, name it, 
and place it in the `config` folder for that file type (e.g. `config\hdf` for new `hdf` file configurations).
If you have installed the labelling tool in editable mode, it should recognise the new file.
