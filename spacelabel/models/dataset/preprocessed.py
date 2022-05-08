from pathlib import Path
from typing import Optional, Dict, List

import numpy
from astropy.time import Time
from h5py import File

from spacelabel.models.dataset import DataSet
from spacelabel.models.dataset.hdf5 import log


class DataSetPreprocessed(DataSet):
    """
    Dataset intended for reading in pre-processed HDF5 datafiles saved out by the code.

    Preprocessing the frequencies by rescaling the range can take several minutes on slow computers.
    """
    @staticmethod
    def exists_preprocessed(file_path: Path) -> Path:
        """
        Should never be run

        :raises NotImplementedError: if you attempt to call this
        """
        raise NotImplementedError("This is the pre-processed dataset class itself")

    def __init__(
            self,
            file_path: Path,
            config_name: Optional[str] = None,
            log_level: Optional[int] = None
    ):
        """
        Sets up a datafile for reading.

        :param file_path: The path to the file
        :param config: The configuration file to use, if any
        :param log_level: The level of logging to show from this object
        """
        super().__init__(
            file_path=file_path.with_suffix('').with_suffix(''), config_name=config_name, log_level=log_level
        )

        file: File = File(file_path)
        self._time = Time(file['Time'], format='jd')

        if log_level:
            log.setLevel(log_level)

    def load(self):
        """
        Similar to the deferred load from above, but takes into account the
        """
        log.info(f"DataSetPreprocessed: Loading '{self._file_path}.preprocessed.hdf5'...")
        file: File = File(self._file_path.with_suffix('.preprocessed.hdf5'))

        names: List[str] = list(file.keys())

        self._observer = file.attrs['observer']

        names.remove('Frequency')
        self._freq = numpy.array(file['Frequency'])
        self._units['Frequency'] = file['Frequency'].attrs['units']

        names.remove('Time')
        self._time = Time(file['Time'], format='jd')
        self._units['Time'] = file['Time'].attrs['units']

        for name in names:
            # KEY DIFFERENCE TO NORMAL HDF5 READIN: We don't transpose here, as the preprocessed datasets are time major
            self._data[name] = numpy.array(file[name])
            self._units[name] = file[name].attrs['units']

    def preprocess(
            self,
            frequency_resolution: Optional[int] = None,
            time_minimum: Optional[float] = None,
    ):
        """
        As this file is already preprocessed, do nothing unless the user
        This does nothing, unless the user has tried to specify pre-processing settings.
        """
        if frequency_resolution or time_minimum:
            raise ValueError(
                f"preprocess: This file has already been pre-processed!\n"
                f"Please delete the pre-processed save file '{self._file_path}.preprocessed.hdf5' "
                f"to change preprocess settings.\n"
            )