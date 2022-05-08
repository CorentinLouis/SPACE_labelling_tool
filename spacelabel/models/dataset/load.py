import logging

from pathlib import Path
from typing import Dict, Type

from spacelabel.models.dataset import DataSet
from spacelabel.models.dataset.hdf5 import DataSetHDF5
from spacelabel.models.dataset.preprocessed import DataSetPreprocessed
from spacelabel.models.dataset.cdf import DataSetCDF

# Registry of dataset file types, as 'suffix' '
DATASET_TYPES: Dict[str, Type['DataSet']] = {
    # e.g. '.csv': DataSetCSV added via modules
    '.hdf5': DataSetHDF5,
    '.cdf': DataSetCDF
}


def load_dataset(
        file_path: Path, config: Dict,
        log_level: int = logging.INFO
) -> DataSet:
    """
    Select the correct type of dataset from file, and load it.

    Needs to check to see if you've tried to open a preprocessed file,
    if not finds the file type and asks it if a preprocessed file for that file type already exists.
    If not, creates a new one.

    :param file_path: Passed through to the dataset
    :param config: Passed through to the dataset
    :param log_level: Passed through to the dataset
    :return: The initialized dataset
    """

    if {'.preprocessed', '.hdf5'} == set(file_path.suffixes):
        return DataSetPreprocessed(
            file_path=file_path, config=None, log_level=log_level
        )
    else:
        dataset_class = DATASET_TYPES[file_path.suffix]
        preprocessed_file = dataset_class.exists_preprocessed(file_path)
        if preprocessed_file:
            return DataSetPreprocessed(
                file_path=preprocessed_file, config_name=None, log_level=log_level
            )
        else:
            return dataset_class(
                file_path=file_path, config_name=config, log_level=log_level
            )
