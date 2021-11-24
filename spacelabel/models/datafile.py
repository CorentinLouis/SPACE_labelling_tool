import json
import numpy
from abc import ABC, abstractmethod
from datetime import datetime
from numpy import ndarray
from typing import Tuple, Dict, Optional, List
from pathlib import Path
from scipy.io import readsav

from spacelabel.models.feature import Feature
from spacelabel.config import find_config_for_file


class Datafile(ABC):
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

    def get_data_for_time_range(
            self, time_start: datetime, time_end: datetime
    ) -> Tuple[ndarray, ndarray, Dict[str, ndarray]]:
        """
        Returns a dictionary containing the data for the specified time range.
        Implemented as returning a dictionary to make it easier to expand to multiple data types.

        :param time_start: The start of the time range (inclusive)
        :param time_end: The end of the time range (inclusive)
        :return: A dictionary containing the keys 'time', 'freq', 'flux' and possibly 'power' and 'polarisation'
        """
        time_mask = self._time[(time_start <= self._time) & (self._time <= time_end)]
        return self._time[time_mask], self._freq, {key: self._data[key][time_mask] for key in self._data.keys()}

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
        return (self._time[0], self._time[-1])

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


class DatafileCassini(Datafile):
    """
    Contains the data from a Cassini observation datafile.
    """
    def __init__(self, file_path: Path, config_name: Optional[str] = None):
        """
        Reads a Cassini datafile.

        :param file_path: The path to the file
        :param config_name: The name of the config file to use, if any
        """
        self._file_path_base = file_path.with_suffix('')
        sav = readsav(str(file_path), python_dict=True)

        config = find_config_for_file(Path(__file__) / "../../config/cassini/")
        self._observer = config['observer']
        self._units = config['units']

        # We want to rename everything in the data file to 'standard' names to make the code
        # a lot easier to read!
        for name_new, name_original in config['names'].items():
            try:
                sav[name_new] = sav.pop(name_original)
            except KeyError:
                pass

        # We use pop to remove the axes values (time and frequency) from the file,
        # so we can just iterate over what's left to rescale as it's all just data variables.
        self._time = numpy.array(sav.pop('time'), dtype=numpy.datetime64)  # Parse the time column.
        freq_original = sav.pop('frequency')

        # The frequency is spaced logarithmically from f[0]=3.9548001 to f[24] = 349.6542 and then linearly above that
        # So we need to transform the frequency table in a full log table and interpolate the flux table
        self._freq = 10**(
            numpy.arange(
                start=numpy.log10(freq_original[0]),
                stop=numpy.log10(freq_original[-1]),
                step=(numpy.log10(max(freq_original))-numpy.log10(min(freq_original)))/399.0,
                dtype=float
            )
        )

        self._data['flux'] = None

        # These will need rebinning like the flux one
        if sav.has("degree_of_polarisation"):
            self._data['degree_of_polarisation'] = sav['degree_of_polarisation']
        if sav.has("power"):
            self._data['power'] = sav['power']

        # Strip out the units for data types that aren't present in this file
        for key in self._units:
            if key not in self._data:
                self._units.pop(key)

        self.load_features_from_json()
