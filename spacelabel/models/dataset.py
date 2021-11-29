"""
Data sets from satellites.

Should probably have the internal data representation moved from numpy arrays to astropy timeseries.
This would also simplify units.
"""

import json
import numpy
from abc import ABC, abstractmethod
from datetime import datetime
from numpy import ndarray  # Explicit import to make Typing easier

from typing import Tuple, Dict, Optional, List, Union
from pathlib import Path
from scipy.io import readsav

from spacelabel.models.feature import Feature
from spacelabel.config import find_config_for_sav


class DataSet(ABC):
    """
    Contains the data from a spacecraft. Implemented differently for different data file formats.
    This is the *abstract* base class that does not implement loading from file.
    """
    _file_path_base: Path = None
    _observer: str = None
    _time: ndarray = None
    _freq: ndarray = None
    _data: Dict[str, ndarray] = {}  # Private dictionary containing the data for the variables
    _units: Dict[str, str] = {}
    _features: List[Feature] = []
    _presenter = None

    def register_presenter(self, presenter):
        self._presenter = presenter

    def get_data_for_time_range(
            self, time_start: datetime, time_end: datetime,
            measurements: Union[None, str, List[str]] = None
    ) -> Tuple[ndarray, ndarray, Dict[str, ndarray]]:
        """
        Returns a dictionary containing the data for the specified time range.
        Implemented as returning a dictionary to make it easier to expand to multiple data types.

        :param time_start: The start of the time range (inclusive)
        :param time_end: The end of the time range (inclusive)
        :param measurements: The types of parameter to get, all if None
        :return: A dictionary containing the keys 'time', 'freq', 'flux' and possibly 'power' and 'polarisation'
        """
        if measurements and not isinstance(measurements, list):
            measurements = [measurements]

        time_mask = self._time[(time_start <= self._time) & (self._time <= time_end)]
        return self._time[time_mask], self._freq, \
            {key: self._data[key][time_mask] for key in self._data if key in measurements or measurements is None}

    def add_feature(self, name: str, vertexes: ndarray):
        """

        :param name: The name of the feature.
        :param vertexes: A 2-d matplotlib array of coordinates as [time, freq]
        :return:
        """
        self._features.append(
            Feature(name=name, time=vertexes[:, 0], freq=vertexes[:, 1], id=len(self._features))
        )

    def get_features_for_time_range(self, time_start: datetime, time_end: datetime) -> List[Feature]:
        """

        :param time_start: The start of the time range (inclusive)
        :param time_end: The end of the time range (inclusive)
        :return:
        """
        return [
            feature for feature in self._features if feature.is_in_time_range(time_start, time_end)
        ]

    def get_units(self) -> Dict[str, str]:
        return self._units

    def get_time_range(self) -> Tuple[datetime, datetime]:
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
                        "name": "Time-Frequency", "properties": {
                            "time_coords": {
                                "id": "unix",  "name":  "Timestamp (Unix Time)", "unit": "s",
                                "time_origin": "1970-01-01T00:00:00.000Z",
                                "time_scale": "TT"
                            },
                            "spectral_coords": {
                                "name": "Frequency",
                                "unit": self._units['freq']
                            },
                            "ref_position": {"id": self._observer}
                        }
                    }
                },
                file_json
            )

    def load_features_from_json(self):
        """
        Loads the features for this datafile from a JSON file.
        This *should* be called in the constructor. Possibly move this to the superclass constructor?
        """
        if self._file_path_base.with_suffix('.json').exists():
            with open(self._file_path_base.with_suffix('.json'), 'r') as file_json:
                tfcat: Dict = json.load(file_json)

            for feature in tfcat["features"]:
                self.add_feature(
                    name=feature['properties']['feature_type'],
                    vertexes=numpy.array(feature['geometry']['coordinates']),
                )


class DataSetCassini(DataSet):
    """
    Contains the data from a Cassini observation datafile.
    """
    def __init__(
            self, file_path: Path, config: Dict,
            frequency_resolution: Optional[int] = 400,
            sav: Optional[dict] = None
    ):
        """
        Reads a Cassini datafile.

        :param file_path: The path to the file
        :param config: The configuration file to use, if any
        :param frequency_resolution: How many frequency bins to rescale to. Default 400
        :param sav: If the sav file has already been read, pass it through to save time
        """
        self._file_path_base = file_path.with_suffix('')
        self._observer = config['observer']

        if not sav:
            sav = readsav(str(file_path), python_dict=True)

        # We want to rename everything in the data file to 'standard' names to make the code easier to read
        for name_new, name_original in config['names'].items():
            try:
                sav[name_new] = sav.pop(name_original)
            except KeyError:
                pass

        # Copy across the units to our object, then strip out the units for data types that aren't present in this file
        self._units = config['units']
        for key in self._units:
            if key not in self._data:
                self._units.pop(key)

        # We use pop to remove the axes values (time and frequency) from the file,
        # so we can just iterate over what's left to rescale as it's all just data variables.
        self._time = numpy.array(sav.pop('time'), dtype=numpy.datetime64)  # Parse the time column.

        # The frequency is spaced logarithmically from f[0]=3.9548001 to f[24] = 349.6542 and then linearly above that
        # So we need to transform the frequency table in a full log table and interpolate the flux table
        freq_original = sav.pop('frequency')
        self._freq = 10**(
            numpy.arange(
                start=numpy.log10(freq_original[0]),
                stop=numpy.log10(freq_original[-1]),
                step=(numpy.log10(max(freq_original))-numpy.log10(min(freq_original)))/(frequency_resolution-1),
                dtype=float
            )
        )

        # Now save the data (e.g. flux, power, degree of polarisation)
        for key in sav:
            variable = sav.pop(key)
            self._data[key] = numpy.zeros(
                (len(self._freq), len(self._time)), dtype=float
            )
            # This absolutely can be done more efficiently
            for i in range(len(self._time)):
                self._data[key][:, i] = numpy.interp(self._freq, freq_original, variable[:, i])

        self.load_features_from_json()
