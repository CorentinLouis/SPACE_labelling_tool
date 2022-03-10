"""
Data sets from satellites.
"""

import json
import logging
from abc import ABC, abstractmethod
from astropy.time import Time
from numpy import ndarray  # Explicit import to make Typing easier
from pathlib import Path
from tfcat.validate import validate_file
from typing import Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from spacelabel.models.feature import Feature

if TYPE_CHECKING:
    from spacelabel.presenters import Presenter

log = logging.getLogger(__name__)


# The human names of the various measurements.
MEASUREMENT_NAMES = {
    'flux_density': "Flux density",
    'power': "Power",
    'degree_of_polarization': "Degree of polarization",
}


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

    def __init__(self, file_path: Path, log_level: Optional[int] = None):
        """
        Initializes the dataset. Mostly used to set log level.
        """
        self._file_path_base = file_path.with_suffix('')

        if log_level:
            log.setLevel(log_level)
            self._log_level = log_level

    @abstractmethod
    def load_data(self):
        """
        Abstract method for loading the data from file
        """
        pass

    def register_presenter(self, presenter: 'Presenter'):
        """
        Links the dataset to the presenter that manages it.
        """
        self._presenter = presenter

    def get_measurement_names(self) -> List[str]:
        """
        Returns the list of measurement names, for filtering output by
        """
        return list(self._data.keys())

    def validate_dates(self, dates: Tuple[Time, Time]):
        """
        Checks to see if the dates of interest are within the file time range.
        :param dates:
        :raise ValueError: If the dates are out of the time range in the file
        """
        if dates[0] < self._time[0] or dates[1] > self._time[-1]:
            raise ValueError(
                f"Date range {dates[0]}-{dates[1]} is outside of the data file range {self._time[0]}-{self._time[1]}.\n"
                f"Please check your date range is YYYY-MM-DD format."
            )

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
        :return: Astropy Time, numpy frequency array, and a dictionary containing the keys 'flux'
            and possibly 'power' and 'polarization'
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

        log.debug(f"get_data_for_time_range: Times {self._time[time_mask]}")

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
                                "unit": self._units['Frequency']
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
                try:
                    tfcat: Dict = json.load(file_json)
                except json.decoder.JSONDecodeError as e:
                    log.error("load_features_from_json: File is not valid JSON (is it blank?)")

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
