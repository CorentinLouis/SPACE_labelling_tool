.. SPACE_labelling_tool documentation master file, created by
   sphinx-quickstart on Mon Sep 19 10:13:52 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to SPACE_labelling_tool's documentation!
================================================

The SPectrogram Analysis and Cataloguing Environment (SPACE) tool is an interactive python tool designed to label radio emission features of interest in a temporal-spectral map (called “dynamic spectrum”). The Software uses Matplotlib’s Polygon Selector widget to allow a user to select and edit an undefined number of vertices on top of the dynamic spectrum before closing the shape (polygon). Multiple polygons may be drawn on any spectrum, and the feature name along with the coordinates for each polygon vertex are saved into a “.json” file as per the “Time-Frequency Catalogue” (TFCat) format along with other data such as the feature id, observer name, and data units. This paper describes the first official stable release (version 2.0) of the tool.


SPACE is part of the `MASER <https://maser.lesia.obspm.fr>`_ (Measuring Analyzing & Simulating Emissions in Radio frequencies) project. 

.. toctree::
   :maxdepth: 3
   :caption: Contents:

   installation
   quickstart
   usage_examples
   data_dictionary
   developer_documentation
   spacecraft_configurations
   limitations

.. toctree::
   :caption: Appendinx
   
   genindex
