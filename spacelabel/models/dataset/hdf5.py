import logging
import numpy
from astropy.time import Time
from h5py import File
from numpy import ndarray  # Explicit import to make Typing easier
from pathlib import Path
from typing import Dict, Optional

from spacelabel.models.dataset import DataSet
from spacelabel.config import find_config_for_file

log = logging.getLogger(__name__)


class DataSetHDF5(DataSet):
    """
    Contains the data from an HDF5-format observation datafile.
    """
    def __init__(
            self, file_path: Path,
            config: Optional[Dict] = None,
            frequency_resolution: Optional[int] = 400,
            file: Optional[File] = None,
            log_level: Optional[int] = None
    ):
        """
        Reads a datafile in HDF5 format.

        :param file_path: The path to the file
        :param config: The configuration file to use, if any
        :param frequency_resolution: If the frequency should be reinterpolated, to what resolution?
        :param file: If the HDF5 file has already been read, pass it through to save time
        :param log_level: The level of logging to show from this object
        """
        super().__init__(file_path, log_level=log_level)

        self._file_path_base = file_path.with_suffix('')
        self._observer = config['observer']

        log.info(f"DataSetHDF5: Loading '{self._file_path_base}'...")

        if not file:
            file: File = File(file_path)

        if not config:
            config: dict = find_config_for_file(file)

        if log_level:
            log.setLevel(log_level)

        names: Dict[str, str] = config['names']

        # Numpy defaults to using days with 'unix time' as the origin; we want actual Julian dates
        self._time = Time(file[names.pop('Time')], format='jd')
        self._units['Time'] = config['units']['Time']
        self._units['Frequency'] = config['units']['Frequency']

        if not frequency_resolution:
            self._freq = file[names.pop('Frequency')]
            # We use pop to take out the time and frequency names from the dictionary,
            # so 'names' now only contains the dependent variables.

            for name_data, name_file in names.items():
                # For each of the dependent variables in the config file, are any of them present in the file?
                if name_file in file.keys():
                    self._data[name_data] = file[name_file]
                    self._units[name_data] = config['units'][name_data]

        else:
            # The frequency is spaced logarithmically from f[0]=3.9548001 to f[24] = 349.6542 then linearly above that
            # So we need to transform the frequency table in a full log table
            freq_original: ndarray = file[names.pop('Frequency')]
            self._freq = 10**(
                numpy.arange(
                    start=numpy.log10(freq_original[0]),
                    stop=numpy.log10(freq_original[-1]),
                    step=(numpy.log10(max(freq_original))-numpy.log10(min(freq_original)))/(frequency_resolution-1),
                    dtype=float
                )
            )
            # We use pop to take out the time and frequency names from the dictionary,
            # so 'names' now only contains the dependent variables.
            # Names can vary between files, so we have a 'standard' name and a 'name we'll see in the file'

            for name_data, name_file in names.items():
                # For each of the dependent variables in the config file, are any of them present in the file?
                if name_file in file.keys():
                    # If so, we need to interpolate the full variable on our new frequency table
                    # Turn into an array to move into memory, otherwise we do a disk read for each access...
                    variable: ndarray = numpy.array(file[name_file])
                    self._data[name_data] = numpy.zeros(
                        (len(self._freq), len(self._time)), dtype=float
                    )
                    # This absolutely can be done more efficiently
                    for i in range(len(self._time)):
                        self._data[name_data][:, i] = numpy.interp(self._freq, freq_original, variable[:, i])

                    # And do the units
                    self._units[name_data] = config['units'][name_data]

        log.info(f"DataSetHDF5: Initialised '{self._file_path_base}'")
        self.load_features_from_json()
