"""
Data sets from satellites.

Should probably have the internal data representation moved from numpy arrays to astropy timeseries.
This would also simplify units.
"""

import json
import logging
import numpy
from abc import ABC, abstractmethod
from astropy.time import Time
from datetime import datetime
from h5py import File
from numpy import datetime64, ndarray  # Explicit import to make Typing easier
from pathlib import Path
from tfcat.validate import validate_file
from typing import Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from spacelabel.models.feature import Feature
from spacelabel.config import find_config_for_file
if TYPE_CHECKING:
    from spacelabel.presenters import Presenter

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class DataSet(ABC):
    """
    Contains the data from a spacecraft. Implemented differently for different data file formats.
    This is the *abstract* base class that does not implement loading from file.
    """
    _file_path_base: Path = None
    _observer: str = None
    _time: Time = None
    _freq: ndarray = None
    _data: Dict[str, ndarray] = {}  # Private dictionary containing the data for the variables
    _units: Dict[str, str] = {}
    _features: List[Feature] = []
    _presenter: 'Presenter' = None
    _log_level: Optional[int] = None  # Passed to Features

    def register_presenter(self, presenter: 'Presenter', log_level: Optional[int] = None):
        """
        Links the dataset to the presenter that manages it.
        """
        self._presenter = presenter
        if log_level:
            log.setLevel(log_level)
            self._log_level = log_level

    def get_data_for_time_range(
            self, time_start: Time, time_end: Time,
            measurements: Union[None, str, List[str]] = None
    ) -> Tuple[Time, ndarray, Dict[str, ndarray]]:
        """
        Returns a dictionary containing the data for the specified time range.
        Implemented as returning a dictionary to make it easier to expand to multiple data types.

        :param time_start: The start of the time range (inclusive)
        :param time_end: The end of the time range (inclusive)
        :param measurements: The types of parameter to get, all if None
        :return: A dictionary containing the keys 'time', 'freq', 'flux' and possibly 'power' and 'polarisation'
        """
        log.info(f"get_data_for_time_range: From {time_start} to {time_end}")

        if measurements and not isinstance(measurements, list):
            # If the user hasn't specified a list of measurements, convert to a single-entry list for ease of use
            measurements: List = [measurements]

        time_mask: ndarray = (time_start <= self._time) & (self._time <= time_end)
        data: Dict[str, ndarray] = {}
        keys: List[str] = measurements if measurements else self._data.keys()

        for key in keys:
            data[key] = self._data[key][:, time_mask]

        return self._time[time_mask], self._freq, data

    def add_feature(self, name: str, vertexes: List[Tuple[Time, float]]) -> Feature:
        """
        Adds a new feature (either from file or a polyselector on the plot).

        :param name: The name of the feature
        :param vertexes: A 2-d matplotlib array of coordinates as [time, freq]
        :return: The feature added
        """
        self._features.append(
            Feature(
                name=name,
                vertexes=vertexes,
                feature_id=len(self._features),
                log_level=self._log_level
            )
        )
        log.debug(f"add_feature: {name} - {vertexes}")
        return self._features[-1]

    def get_features_for_time_range(self, time_start: Time, time_end: Time) -> List[Feature]:
        """
        Returns the Features that are contained within the specified time range.

        :param time_start: The start of the time range (inclusive)
        :param time_end: The end of the time range (inclusive)
        :return: A list of the features (in feature format)
        """
        return [
            feature for feature in self._features if feature.is_in_time_range(time_start, time_end)
        ]

    def get_units(self) -> Dict[str, str]:
        return self._units

    def get_time_range(self) -> Tuple[Time, Time]:
        """
        Returns the start and end dates in the time window.
        """
        return self._time[0], self._time[-1]

    def write_features_to_text(self):
        """
        Writes a summary of the bounds of the features that have been selected, to text file.
        """
        with open(self._file_path_base.with_suffix('.txt'), 'w') as file_text:
            for feature in self._features:
                file_text.write(f'{feature.to_text_summary()}\n')

    def write_features_to_json(self):
        """
        Writes the details of the bounds of each feature, to a TFCat-format JSON file.
        """
        with open(self._file_path_base.with_suffix('.json'), 'w') as file_json:
            json.dump(
                {
                    "type": "FeatureCollection",
                    "features": [
                        feature.to_tfcat_dict() for feature in self._features
                    ],
                    "crs": {
                        "type": "Cartesian",
                        "name": "Time-Frequency",
                        "properties": {
                            "type": "Cartesian",
                            "name": "Time-Frequency",
                            "time_coords": {
                                "id": "unix",  "name":  "Timestamp (Unix Time)", "unit": "s",
                                "time_origin": "1970-01-01T00:00:00.000Z",
                                "time_scale": "TT"
                            },
                            "spectral_coords": {
                                "name": "Frequency",
                                "unit": self._units['frequency']
                            },
                            "ref_position": {"id": self._observer}
                        }
                    }
                },
                file_json
            )
        log.info(
            f"write_features_to_json: Writing '{self._file_path_base.with_suffix('.json')}'"
        )

    def load_features_from_json(self):
        """
        Loads the features for this datafile from a JSON file.
        This *should* be called in the constructor.
        Possibly move this to the superclass constructor?
        """
        path_tfcat: Path = self._file_path_base.with_suffix('.json')

        if not path_tfcat.exists():
            log.info("load_features_from_json: No existing JSON file")
        else:
            log.info(
                f"load_features_from_json: Loading '{self._file_path_base.with_suffix('.json')}'"
            )
            validate_file(path_tfcat)

            with open(path_tfcat, 'r') as file_json:
                tfcat: Dict = json.load(file_json)

            for feature in tfcat["features"]:
                vertexes = []
                for vertex in feature['geometry']['coordinates'][0]:
                    time = Time(vertex[0], format='unix')
                    time.format = 'jd'  # This step prevents it being list comprehension
                    vertexes.append((time, vertex[1]))

                log.debug(
                    f"load_features_from_json: Adding {feature['properties']['feature_type']} - {vertexes}"
                )
                self.add_feature(
                    name=feature['properties']['feature_type'],
                    vertexes=vertexes
                )


class DataSetCassini(DataSet):
    """
    Contains the data from a Cassini observation datafile.
    """
    def __init__(
            self, file_path: Path,
            config: Optional[Dict] = None,
            frequency_resolution: Optional[int] = 400,
            file: Optional[File] = None,
            log_level: Optional[int] = None
    ):
        """
        Reads a Cassini datafile in HDF5 format.

        :param file_path: The path to the file
        :param config: The configuration file to use, if any
        :param frequency_resolution: How many frequency bins to rescale to. Default 400
        :param file: If the HDF5 file has already been read, pass it through to save time
        :param log_level: The level of logging to show from this object
        """
        self._file_path_base = file_path.with_suffix('')
        self._observer = config['observer']

        log.info(f"DataSetCassini: Loading '{self._file_path_base}'...")

        if not file:
            file: File = File(file_path)

        if not config:
            config: dict = find_config_for_file(file)

        if log_level:
            log.setLevel(log_level)

        names: Dict[str, str] = config['names']

        # Numpy defaults to using days with 'unix time' as the origin; we want actual Julian dates
        self._time = Time(file[names.pop('time')], format='jd')
        self._units['time'] = config['units']['time']

        # The frequency is spaced logarithmically from f[0]=3.9548001 to f[24] = 349.6542 and then linearly above that
        # So we need to transform the frequency table in a full log table
        freq_original: ndarray = file[names.pop('frequency')]
        self._freq = 10**(
            numpy.arange(
                start=numpy.log10(freq_original[0]),
                stop=numpy.log10(freq_original[-1]),
                step=(numpy.log10(max(freq_original))-numpy.log10(min(freq_original)))/(frequency_resolution-1),
                dtype=float
            )
        )
        self._units['frequency'] = config['units']['frequency']

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

        log.info(f"__init__: Initialised Cassini dataset '{self._file_path_base}'")
        self.load_features_from_json()
