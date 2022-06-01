"""
Data sets from satellites.
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, TYPE_CHECKING, Type

import math
import numpy
from astropy.timeseries import TimeSeries, aggregate_downsample
from astropy.time import Time, TimeDelta
from astropy import units
from h5py import File
from numpy import ndarray  # Explicit import to make Typing easier
from pandas import DataFrame
from tfcat.validate import validate_file
from tqdm import trange


from spacelabel.models.feature import Feature

if TYPE_CHECKING:
    from spacelabel.presenters import Presenter

log = logging.getLogger(__name__)


class DataSet(ABC):
    """
    Contains the data from a spacecraft. Implemented differently for different data file formats.
    This is the *abstract* base class that does not implement loading from file.
    """
    _file_path: Path = None  # The suffix-less file path
    _observer: str = None
    _time: Time = None
    _freq: ndarray = None
    _data: Dict[str, ndarray] = {}  # Private dictionary containing the data for the variables
    _units: Dict[str, str] = {}
    _features: List[Feature] = []
    _presenter: 'Presenter' = None
    _log_level: Optional[int] = None  # Passed to Features
    _config: Optional[Dict] = None  # The configuration used

    @staticmethod
    @abstractmethod
    def exists_preprocessed(file_path: Path) -> Path:
        """
        Does a pre-processed file already exist for this path?

        :raises NotImplementedError: if not implemented for this DataSet
        :return: The path to the preprocessed file
        """
        raise NotImplementedError("A dataset must have the ability to look for pre-processed versions of itself")

    def __init__(self, file_path: Path, config_name: Optional[str] = None, log_level: Optional[int] = None):
        """
        Initializes the dataset. Mostly used to set log level.

        Will do basic loading in, but we don't want to load everything on initialization as the dates proposed may
        be out of the file range, so defer until we've tested those.

        :param file_path: The path to the file
        :param config_name: The name of the configuration file to use, if any. Should be handled in subclass
        :param log_level: The level of logging to show from this object
        """
        self._file_path = file_path

        if log_level:
            log.setLevel(log_level)
            self._log_level = log_level

        self.load_features_from_json()

    @abstractmethod
    def load(self):
        """
        Implemented in the specific subtypes, this loads the data from file.
        Deferred load as we only want to part-load e.g. dates for quick validation.

        :raises NotImplementedError: if not implemented for this DataSet
        """
        raise NotImplementedError("A dataset must have deferred loading code")

    def preprocess(
        self,
        frequency_resolution: Optional[int] = None,
        time_minimum: Optional[float] = None,
    ):
        """
        Rescales the frequency and/or time, and all measurements depending on them, then saves to an HDF5 file.

        :param frequency_resolution: The number of frequency bins to rescale to (optional, positive).
        :param time_minimum: The minimum time bin width, in seconds (optional, positive).
        """
        if not frequency_resolution:
            frequency_resolution = self._config['preprocess'].get('frequency_resolution', None)
        if frequency_resolution:
            if frequency_resolution < 0:
                raise ValueError(f"Requested a negative frequency resolution: {frequency_resolution}")

        if not time_minimum:
            time_minimum = self._config['preprocess'].get('time_minimum', None)
        if time_minimum:
            if time_minimum < 0:
                raise ValueError(f"Requested a negative minimum time bin: {time_minimum}")
            elif TimeDelta(time_minimum, format='sec') < (self._time[1] - self._time[0]):
                log.warning("preprocess: The target time bin is smaller than the time bins in the data; skipping.")
                time_minimum = None

        if frequency_resolution:
            freq_original: ndarray = self._freq
            freq_rescaled: ndarray = 10 ** (
                numpy.arange(
                    start=numpy.log10(freq_original[0]),
                    stop=numpy.log10(freq_original[-1]),
                    step=(
                        numpy.log10(max(freq_original)) - numpy.log10(min(freq_original))
                    ) / (frequency_resolution - 1),
                    dtype=float
                )
            )

            # ====== THIS ISN'T DEPRECATED CODE! THIS IS THE EXAMPLE I WAS WORKING FROM ======
            # f_new = 10 ** (np.arange(np.log10(frequency[0]), np.log10(frequency[-1]),
            #                          (np.log10(max(frequency)) - np.log10(min(frequency))) / 399, dtype=float))
            # data_new = np.zeros((f_new.size, len(time)), dtype=float)
            # for i in range(len(time)):
            #     data_new[:, i] = np.interp(f_new, frequency, data[:, i])
            # ================================================================================

            log.info(
                f"preprocessing: Rebinning frequency of {len(self._data.keys())} "
                f"measurements to {frequency_resolution} bins..."
            )
            for name, measurement_original in self._data.items():
                # Turn into an array to move into memory, otherwise we do a disk read for each access...
                measurement_new = numpy.zeros(
                    (
                        len(self._time),
                        len(freq_rescaled)
                    ), dtype=float
                )

                for i in trange(len(self._time)):
                    measurement_new[i, :] = numpy.interp(
                        x=freq_rescaled,
                        xp=freq_original,
                        fp=measurement_original[i, :]
                    )
                    self._data[name] = measurement_new

            self._freq = freq_rescaled

        if time_minimum:
            # If we're rescaling the time resolution, do that.
            log.info(
                f"preprocessing: Downsampling time bin width of {len(self._data.keys())} "
                f"measurements to {time_minimum} seconds... this might take a while!"
            )

            time_original: Time = self._time
            
            
            
            time_rescaled: Time = TimeSeries(
                time_start=time_original[0],
                time_delta=time_minimum * units.s,
                n_samples=math.ceil((time_original[-1] - time_original[0]).to(units.s).value/time_minimum)
            ).time


            for name, measurement_original in self._data.items():
                log.info(
                    f"preprocessing: Downsampling time of {len(self._data.keys())} "
                    f"by a factor of 1/{(time_minimum)/(time_original[1]-time_original[0]).to(units.s)}"
                )
                measurement_new = numpy.zeros(
                    (
                        len(time_rescaled),
                        len(self._freq)
                    )
                )
                
                
                for i in range(0, len(self._freq)):
                    measurement_new[:, i] = numpy.interp(
                        time_rescaled.value, time_original.value, measurement_original[:, i]
                        )
                        
                self._data[name] = measurement_new

                self._time = time_rescaled

        if time_minimum or frequency_resolution:
            self.save_to_hdf()

    def save_to_hdf(self):
        """
        Saves the data to disk as a pre-processed HDF5 file.
        """
        output_file = File(
            self._file_path.with_suffix('.preprocessed.hdf5'), 'w'
        )
        output_file.attrs.create('observer', self._observer)

        # Has to be done differently as this is an Astropy quantity
        output_file.create_dataset('Time', data=numpy.array(self._time.jd1+self._time.jd2))
        output_file['Time'].attrs.create('units', self._units['Time'])

        output_file.create_dataset('Frequency', data=self._freq)
        output_file['Frequency'].attrs.create('units',  self._units['Frequency'])

        for key, value in self._data.items():
            output_file.create_dataset(key, data=value, compression='lzf')
            output_file[key].attrs['units'] = self._units[key]

        output_file.close()

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
                f"Date range {dates[0]} to {dates[-1]} is outside of the data file range "
                f"{self._time[0].to_datetime()} to {self._time[1].to_datetime()}.\n"
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
        log.info(f"get_data_for_time_range: From {time_start} ({time_start.jd}) to {time_end} ({time_end.jd})")

        if measurements and not isinstance(measurements, list):
            # If the user hasn't specified a list of measurements, convert to a single-entry list for ease of use
            measurements: List = [measurements]

        time_mask: ndarray = (time_start <= self._time) & (self._time <= time_end)
        data: Dict[str, ndarray] = {}
        keys: List[str] = measurements if measurements else self._data.keys()

        for key in keys:
            data[key] = self._data[key][time_mask, :]

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


    def get_frequency_range(self) -> Tuple[float, float]:
        """
        Returns the min and max of the frequency range
        """
        return numpy.min(self._freq), numpy.max(self._freq)

    def get_bbox(self) -> Tuple[Time, float, Time, float]:
        """
        Returns the time and frequency limits of the plotting window
        """
        times = self.get_time_range()
        freqs = self.get_frequency_range()
        return times[0], freqs[0], times[1], freqs[1]

    def write_features_to_text(self):
        """
        Writes a summary of the bounds of the features that have been selected, to text file.
        """
        with open(self._file_path.with_suffix('.txt'), 'w') as file_text:
            for feature in self._features:
                file_text.write(f'{feature.to_text_summary()}\n')

    
    def write_features_to_json(self):
        """
        Writes the details of the bounds of each feature, to a TFCat-format JSON file.
        """
        bbox = self.get_bbox()
        with open(self._file_path.with_suffix('.json'), 'w') as file_json:
            json.dump(
                {
                    "type": "FeatureCollection",
                    "features": [
                        feature.to_tfcat_dict(bbox=bbox) for feature in self._features
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
            f"write_features_to_json: Writing '{self._file_path.with_suffix('.json')}'"
        )

    def load_features_from_json(self):
        """
        Loads the features for this datafile from a JSON file.
        """
        path_tfcat: Path = self._file_path.with_suffix('.json')

        if not path_tfcat.exists():
            log.info("load_features_from_json: No existing JSON file")
        else:
            log.info(
                f"load_features_from_json: Loading '{self._file_path.with_suffix('.json')}'"
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
