# SPACE Labelling Tool

Utility to allow for identification of radio features from spacecraft observations via a GUI.


## Getting Started

Clone this repository, and then install it in 'editable' mode as:
```shell
git clone https://github.com/CorentinLouis/SPACE_labelling_tool.git
pip install -e SPACE_labelling_tool
```
Installing in editable mode will allow the scripts to read any new or modified versions of the configuration files.

To use the development version of the tool, after installing do:
```shell
cd SPACE_labelling_tool
git switch develop
```

## Usage

```shell
space_label.py [-h] [-s SPACECRAFT] FILE DATE DATE
```

**Positional arguments:**
* `FILE`: The name of the IDL `.sav` file to analyse. 
  It must be in the format outlined in the [data_dictionary](docs/data_dictionary.md); three (or more) columns!
* `DATE`: The window of days to plot, in ISO YYYY-MM-DD format, e.g. '2003-12-1 2003-12-31' for December 2003.
  The data will be scrolled through in blocks of this window's width.

**Optional arguments:**
* `-h`, `--help`: Shows help documentation.
* `-s SPACECRAFT`: The name of the spacecraft. Auto-detected from the input file columns, 
  but required if multiple spacecraft describe the same input file. Valid options are: cassini, juno.

The code will attempt to identify which spacecraft the data file format corresponds to, and read the file intelligently.
If it can't fit one of them, it will prompt the user to create a new spacecraft configuration file.
In the case of a file matching multiple spacecraft formats, the user is prompted to select one.


### Usage Examples

Calling the code as:
```shell
space_label.py cassini_data.sav 2004001 2004035
```
Will load the file `cassini_data.sav`, and display the radio observations
for the time window 1/1/2004 to 4/2/2004.


## Documentation

Spacecraft configuration files are stored in the `config/` directory in JSON format. 
For more info on how to create a new one, see [spacecraft configurations](docs/spacecraft_configurations.md).

Information on the file formats this program inputs and outputs can be found in the [data dictionary](docs/data_dictionary.md).



==============================================================

# SPACE Labelling Tool Development 

This is the development stage for updates to the SPACE project. 
The current version of this tool has the same functionality as the principal one located in the master branch with an extra feature. 
This version allows for a smoother user interface by incorporating the arrow keys as a way to scroll between time phases on the spectrogram. 
This substitutes the need for the program to ask the user if they wish to continue or not and if they wish to go backwards or forwards, 
with the simple press of the left or right arrow key (left going back in time and right going forwards). 
Similar to the version, stacie_develop.py uses Matplotlib's Polygon Selector widget to allow a user to select and edit a number of polygons on top of a spectrogram, 
of which the feature name along with the maximum and minimum time and frequency points are saved into a ".txt" file, 
while the coordinates for each polygon vertex are saved into a ".json" file as per the TFCat format, 
along with information on the observer/experiment and the units of measurement. 
These files are saved into the user's local directory with the names "selected_polygons.txt" and "polygonData.json". 
Currently, this version only works when ran on the terminal or in Spyder when run on a Mac. 
The backend specified for operation on Spyder in Windows (PyQt5) causes issues which are detailed below.

## Usage Instructions

This tool operates in many the same ways as the main version, in the master branch of this repository. 
The user is first asked to input the name / directory of the data file from which they wish to plot, 
along with the year of origin of the data. 
This file must be in a ".sav" format with the time data in either doy format or yyyyddd format. 
Once this is entered the program asks the user for the name of the time, frequency and flux variables in the data file. 
A prompt asking for observer name and frequency units appears (information which is saved to the ".json" file as per TFCat format). 
Finally the user is asked for the start and end day which they wish to examine (in yyyddd format). 
The plot is then created (with previously drawn polygons overlaid if relevant) and the user is asked to input the name of the first feature they wish to catalogue. 

NOTE: When ran in the terminal, the plot appears before the user is prompted to input a feature name, 
however on Spyder this is not the case as the user must input the name of the first feature "blindly." 
It is recommended that in this case a sample name is typed in to allow the user to see the plot, 
and then if a feature is required to be labelled, they can rename the feature using the instructions below. 

Once the plot has appeared and the name of the feature is entered the user may interact with the figure and draw polygons ontop of it. 
This is done using the cursor which will be shadowed by a grey circle on the plot, 
each time the user clicks on a point a grey circle will be left at that point and act as a vertex for the polygon. 
Subsequent vertices will be joined together by a similarly grey dashed line, 
to close the polygon the user must return and click on the first vertex. 
At this point the user may edit the shape of the polygon by drag and dropping any vertex of their choice.

The use of the following keys allows for further interaction :
* "esc" - hitting this key clears and deletes any polygons that have been drawn on the current plot, and these will not be saved to the file.
* "enter" - this allows the user to start drawing another polygon, however prior to drawing the user will be asked to input a name for the feature they are about to draw.
* "q" - once this key is hit the figure will close and the polygons drawn will be saved to the files
* "r" - this allows the user to rename the polygon that has just been or currently is being drawn

Once the user has finished drawing their polygons they may hit "q" to close the window and end the program or, 
if they wish to go to either the next or previous time phase they can do so by hitting the left or right arrow keys. 
Hitting "left" will create a new environment with data form the previous time range, 
and similarly when pressing "right" but with the next data in time. Once again, if running on Spyder, 
a feature name will need to be inputted prior to the plot becoming visible, 
but this can be easily worked around by using the renaming feature. 

## Issues

The main issue currently facing this program is its lack of cross compatibility between Mac and Windows when run in Spyder. 
The program specifies the use of the PyQt5 backend when run through Spyder in Windows, this is to ensure that the principle features of SPACE work as designed. 
However, it is this backend that prevents the scrolling with the arrow keys feature from working when run by a Windows machine. 
When this occurs a QCoreApplication error appears : "QCoreApplication::exec: The event loop is already running." 
Further testing is required to determine if other backends will support all features on Spyder ran on Windows Machines. 
The MacOSX backend allows the scrolling feature to work properly and without issue. 

Furthermore, as with the main version of SPACE the bug where the plot does not appear until after the user has inputted a feature label (on Windows or Mac) is one to note. 
Again, this does not happen when run on the terminal. 
It is believed that is due to the order in which Spyder runs and evaluates the lines of the code compared to the terminal, 
however no solution has been determined yet. 

## Python Requirements
Spyder - 4.1.5 
Python - 3.8.5

Matplotlib - 3.4.2
SciPy - 1.6.3
NumPy - 1.20.2
shapely - 1.8.0
