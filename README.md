# SPACE Labelling Tool

Utility to allow for identification of radio features from spacecraft observations via a GUI.

## Getting Started

Clone this repository, and then install it in 'editable' mode as:

```shell
git clone https://github.com/CorentinLouis/SPACE_labelling_tool.git
pip install -e SPACE_labelling_tool
```
Installing in editable mode will allow the scripts to read any new or modified versions of the configuration files.

## Usage

```shell
spacelabel [-h] [-s SPACECRAFT] FILE DATE DATE
```

**Positional arguments:**
* `FILE`: The name of the `.hdf5` or `.cdf` file to analyse. 
  It must be in the format outlined in the [data_dictionary](docs/data_dictionary.md); three (or more) columns!
* `DATE`: The window of days to plot, in ISO YYYY-MM-DD format, e.g. '2003-12-01 2003-12-31' for December 2003.
  The data will be scrolled through in blocks of this window's width.

**Optional arguments:**
* `-h`, `--help`: Shows help documentation.
* `-s SPACECRAFT`: The name of the spacecraft. Auto-detected from the input file columns, 
  but required if multiple spacecraft describe the same input file.
* `-f FREQUENCY`: How many log-space frequency bins to rebin the data to. Overrides any default for the spacecraft.
* `-t TIME_MINIMUM`: How small the minimum time bin should be, in seconds. This must be an even multiple of the current 
  time bins, e.g. a file with 1s time bins could have a minimum time bin of 15s.
* `-frac_dyn_range FRAC_DYN_RANGE FRAC_DYN_RANGE`: The minimum and maximum fraction of the flux to be display in the dynamic range (by default: 0.05 0.95)
* `-cmap CMAP`: The name of the color map that will be used for the intensity plot (by default: viridis)
* `-g [FREQUENCY_GUIDE [FREQUENCY_GUIDE ...]]`: Creates horizontal line(s) at specified frequencies to aid with labeling. Lines can be toggled using check boxes.
* `--not_verbose`: If not_verbose is called, the debug log will not be printed. By default: verbose mode


The code will attempt to identify which spacecraft the data file format corresponds to, and read the file intelligently.
If it can't fit one of them, it will prompt the user to create a new spacecraft configuration file.
In the case of a file matching multiple spacecraft formats, the user is prompted to select one.

### GUI

Once the file has loaded, it launches a GUI for selecting the measurements within the file to display, 
and then to navigate the data selected. 
The plot will display the time range selected, plus 1/4 of the previous window.

There are the following interactive components:
* **Measurements:** Each pane displays a measurement, with name, scale and units on the right. 
  Features can be drawn by clicking to add coordinates, and completed by clicking on the first coordinate added again. The vertices of the polygon can be modified before completed the polygon:
  * Hold _ctrl_ and click and drag a vertex to reposition it before the polygon has been completed.
  * Hold the _shift_ key and click and drag anywhere in the axes to move all vertices.
  * Press the _esc_ key to start a new polygon.

  Once selected, a feature can be named. Features can be selected on any pane, and will be mirrored on all other panes.
* **Prev/Next buttons:** These move through the data by an amount equal to the width of time range selected. 
  This will also overlap 1/4 of the current window as 'padding'.
* **Save button:** This will save any features to TFcat JSON format, as `catalogue_{OBSERVER_NAME}.json`.

Once finished, you can save and then close the figure using the normal close button.

### Usage Examples

Calling the code as:
```shell
space_label.py cassini_data.hdf5 2006-02-10 2006-02-11
```
Will load the file `cassini_data.hdf5`, and prompt the user to select which measurements to display:

![Example starting window](docs/images/select-measurements.png)

Once selected, the radio observations will be displayed
for the time window 10/2/2006 to 11/2/2006:

![Example starting window](docs/images/display-measurements.png)

## Documentation

Spacecraft configuration files are stored in the `config/` directory in JSON format. 
For more info on how to create a new one, see [spacecraft configurations](docs/spacecraft_configurations.md).

Information on the file formats this program inputs and outputs can be found in the [data dictionary](docs/data_dictionary.md).

## Limitations & Future Work

* The performance of the MatPlotLib-based front-end is poor for high-resolution plots. 
  Future work would involve re-implementing the front-end in a more modern library like Plotly.
* The code loads all the data provided into memory at launch. This limits its scalability.
  Future work would involve re-saving provided data as `parquet` or other time-indexable files for partial loads
  using the Dask and XArray libraries.
* Add configurations that load data directly from catalogues.

## Terminology

* 'Polarization' has been chosen over 'Polarisation' as it is the Oxford standard for the spelling.
