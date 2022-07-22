# Developer Documentation

The SPACE Labelling Tool is designed using an object-oriented Model-View-Presenter structure. 
There are three components:

* **Model:** This is the representation of the data, along with the methods required to access and modify it.
* **View:** This is the GUI for presenting the data.
* **Presenter:** This is the glue between the two, that takes requests from the **View**, 
  collects data from the **Model**, and sends it back to the **View**. This allows for easy modularity.
  *The Model and View should never talk directly*.

## Model

The core part of the model, and the bit that is relevant to future expansion, is the **DataSet**. 
A **DataSet** holds one or more sets of data, along with the frequency and time axis data on them, and the data required
to output them to **TFCat** JSON format. **DataSet** is an abstract class, that is extended for each new file type.

For examples of new file types, look at the [HDF](../spacelabel/models/dataset/hdf.py) and 
[CDF](../spacelabel/models/dataset/cdf.py) implementations. A new **DataSet** for a new file type must include:

* `exists_preprocessed`: A static method which checks to see if a pre-processed version of the file exists.
  If one exists, it will be `filename.preprocessed.hdf5`, where `filename` is set in `__init__` (see next!).
* `__init__`: An initialization method which loads the time range from the file, 
  so it can be validated against the time range the user requested without having to load the whole file.
  It also sets the `filename`. If it is `filename.csv` or similar, then when the code saves a preprocessed file
  or a **TFCat** JSON file, it will save it to `filename.preprocessed.hdf5`, `filename.json`.
* `load`: A method which loads the full contents of the data into memory. 

Models also exist for the polygons stored on a plot. These should not need modifying.

## View

This is the bit 