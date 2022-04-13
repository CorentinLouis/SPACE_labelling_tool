import logging
import numpy
from astropy.time import Time
from h5py import File
from numpy import ndarray  # Explicit import to make Typing easier
from pathlib import Path
from tqdm import trange
from typing import Dict, Optional, List

from spacelabel.models.dataset import DataSet
from spacelabel.config import find_config_for_file

log = logging.getLogger(__name__)


class DataSetHDF5(DataSet):
    """
    Contains the data from an HDF5-format observation datafile.
    """
    def __init__(
            self,
            file_path: Path,
            config: Optional[Dict] = None,
            log_level: Optional[int] = None
    ):
        """
        Sets up a datafile for reading.

        :param file_path: The path to the file
        :param config: The configuration file to use, if any
        :param log_level: The level of logging to show from this object
        """
        super().__init__(file_path, log_level=log_level)

        file: File = File(file_path)
        self._file_path = file_path.with_suffix('')

        # Find a configuration, or validate the one we have been passed
        if not config:
            self._config: dict = find_config_for_file(list(file.keys()))
        else:
            if not set(file.keys()) - config['names'].values():
                self._config = config
            else:
                raise KeyError("The specified configuration does not fully describe the file!")

        if log_level:
            log.setLevel(log_level)

        # Save time so we can validate the dates
        self._time = Time(file[self._config['names']['Time']], format='jd')
        self._units['Time'] = self._config['units']['Time']

    def load(
            self,
            frequency_resolution: Optional[int] = 400,
    ):
        """
        Reads a datafile in HDF5 format using the config file set earlier.

        :param frequency_resolution: If the frequency should be re-interpolated, to what resolution?
        """
        self._observer = self._config['observer']

        log.info(f"DataSetHDF5: Loading '{self._file_path.with_suffix('.hdf5')}...")
        file: File = File(self._file_path.with_suffix('.hdf5'))

        names: Dict[str, str] = self._config['names']

        # Numpy defaults to using days with 'unix time' as the origin; we want actual Julian dates
        self._time = Time(file[names.pop('Time')], format='jd')
        self._units['Time'] = self._config['units']['Time']

        self._units['Frequency'] = self._config['units']['Frequency']

        self._freq = file[names.pop('Frequency')]
        # We use pop to take out the time and frequency names from the dictionary,
        # so 'names' now only contains the dependent variables.

        for name_data, name_file in names.items():
            # For each of the dependent variables in the config file, are any of them present in the file?
            if name_file in file.keys():
                self._data[name_data] = file[name_file]
                self._units[name_data] = self._config['units'][name_data]

        if frequency_resolution:
            self.rescale_frequency(frequency_resolution)

        log.info(f"DataSetHDF5: Loaded '{self._file_path}'")


class DataSetPreprocessed(DataSet):
    """
    Dataset intended for reading in pre-processed HDF5 datafiles saved out by the code.

    Preprocessing the frequencies by rescaling the range can take several minutes on slow computers.
    """
    def __init__(
            self,
            file_path: Path,
            config: Optional[Dict] = None,
            log_level: Optional[int] = None
    ):
        """
        Sets up a datafile for reading.

        :param file_path: The path to the file
        :param config: The configuration file to use, if any
        :param log_level: The level of logging to show from this object
        """
        super().__init__(file_path, config, log_level)

        file: File = File(self._file_path.with_suffix('.preprocessed.hdf5'))
        self._time = Time(file['Time'], format='jd')

        if log_level:
            log.setLevel(log_level)

    def load(self):
        """
        Similar to the deferred load from above, but takes into account the
        """
        log.info(f"DataSetHDF5: Loading '{self._file_path.with_suffix('.preprocessed.hdf5')}...")
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
            self._data[name] = numpy.array(file[name])
            self._units[name] = file[name].attrs['units']

# Remember to register datatypes in the datatype reader!
