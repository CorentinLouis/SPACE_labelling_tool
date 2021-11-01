# SPACE Labelling Tool v1.1.0

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5636922.svg)](https://doi.org/10.5281/zenodo.5636922)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## Title: SPectrogram Analysis and Cataloguing Environment (SPACE) 
 
SPACE is an interactive python tool designed to label features of interest on a dynamic spectrum and to save the time-frequency coordinates to both ".txt" and ".json" files. The program uses Matplotlib's Polygon Selector widget to allow a user to select and edit an undefined amount of vertices on top of the dynamic spectrum before closing the shape (polygon). Multiple polygons may be drawn on any spectrum, of which the feature name along with the maximum and minimum time and frequency points are saved into a ".txt" file, while the coordinates for each polygon vertex are saved into a ".json" file as per the TFCat format along with other data such as the feature id, observer name, and data units. These files are saved into the user's local directory with the names "selected_polygons.txt" and "polygonData.json". The program can be run on the terminal or in a Spyder environment, in which case it specifies the need for the PyQt5 backend, this is implemented in the code itself.

NOTE: When run in the Spyder environment, due to a glitch, the inital spectrogram does not appear before the user is asked to input the name of the first feature. However, in the terminal this is not an issue and the user has the ability to view the spectrogram before begining to label. It is therefore recommended for optimal performance that SPACE is ran in the terminal. If ran in Spyder, it is recomended that the user "blindly" inputs a feature name for the first polygon, and once completed drawing, renames the feature they have labelled using the instructions below. 
 
## Usage instructions:
 
 The program begins by asking the user several questions related to the data file as well as the user's requirements. It first asks for the name/location of the data file from which the dynamic spectrum will be constructed along with the year of origin of the data. The data file must be in a ".sav" format. Once an appropriate file has been selected the user is asked to input the name of the variables used in the ".sav" file to index the time, frequency and flux values. Following this it asks for the name of the instrument / data observer along with the units of measurement. This information will be saved into the ".json" file. In cany case where the user is aksed to input multiple values, each value/name must be seperated by a comma and a space (e.g. ", "). 
 
 The user will then be asked to input a time range for the spectrum (start and end days in yyyyddd format). This will be followed by the program asking the user to input a name for feature of which they are drawing (when run in Spyder the spectrogram will not appear until the user has done so). Once inputted, the spectrogram appears and the user may begin drawing the polygon. This is done using the cursor which will be shadowed by a grey circle on the plot, each time the user clicks on a point a grey circle will be left at that point and act as a vertex for the polygon. Subsequent vertices will be joined together by a similarly grey dashed line, to close the polygon the user must return and click on the first vertex. At this point the user may edit the shape of the polygon by drag and dropping any vertex of their choice. 
 
 The use of the following keys allows for further interaction :
 
 "esc" - hitting this key clears and deletes any polygons that have been drawn on the current plot, and these will not be saved to the file.
 
 "enter" - this allows the user to start drawing another polygon, however prior to drawing the user will be asked to input a 
 name for the feature they are about to draw. 
 
 "q" - once this key is hit the figure will close and the polygons drawn will be saved to the files
 
 "r" - this allows the user to rename the polygon that has just been or currently is being drawn
 
 Once the user has has finished drawing their polygons they are required to hit "q" or close the windoow close to proceed. The program will then ask if they wish to continue and move to the next time phase. If so, they will subsequently be asked to specify if they wish go forward or backward in time. Once copmleted, a new spectrum will be plotted with the same time range as originally specified and with a layover of one day. Any polygons that have been previously drawn and saved to the data files will be shown in the new figure, but these are not editable and are fixed for reference only. 
 
## Python Requirements:
 
 Spyder - version 4.1.5 
 Python - 3.8.5

 matplotlib - 3.4.2
 scipy - 1.6.3
 numpy - 1.20.2
 shapely - 1.8.0
 

