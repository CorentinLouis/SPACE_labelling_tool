import logging

from pathlib import Path
from typing import Dict, Type

from spacelabel.models.dataset import DataSet
from spacelabel.models.dataset.hdf5 import DataSetHDF5, DataSetPreprocessed

# Registry of dataset file types, as 'suffix' '
DATASET_TYPES: Dict[str, Type['DataSet']] = {
    # e.g. '.csv': DataSetCSV added via modules
    '.hdf5': DataSetHDF5
}


def load_dataset(
        file_path: Path, config: Dict,
        log_level: int = logging.INFO
) -> DataSet:
    """
    Select the correct type of dataset from file, and load it.

    :param file_path: Passed through to the dataset
    :param config: Passed through to the dataset
    :param log_level: Passed through to the dataset
    :return: The initialised dataset
    """

    if file_path.with_suffix('.preprocessed.hdf5').exists():
        return DataSetPreprocessed(
            file_path=file_path, config=None, log_level=log_level
        )
    elif '.hdf5' in file_path.suffixes and '.preprocessed' in file_path.suffixes:
        return DataSetPreprocessed(
            file_path=file_path, config=None, log_level=log_level
        )
    else:
        return DATASET_TYPES[file_path.suffix](
            file_path=file_path, config=config, log_level=log_level
        )
