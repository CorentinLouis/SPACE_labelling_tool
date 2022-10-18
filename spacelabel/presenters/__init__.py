import logging

from astropy.time import Time, TimeDelta
from datetime import datetime, timedelta
from numpy import datetime64
from typing import List, Optional, Tuple, Dict
import numpy
from shapely.geometry import Polygon,box
from spacelabel.models.dataset import DataSet
from spacelabel.models.feature import Feature
from spacelabel.views.matplotlib import ViewMatPlotLib

OVERLAP_FRACTION = 0.25  # Default fraction of window to use as overlap when panning through data

log = logging.getLogger(__name__)


class Presenter:
    """

    """
    _dataset: DataSet = None
    _view: ViewMatPlotLib = None
    _time_start: Time = None
    _time_end: Time = None
    _fig_size: Tuple[float, float] = None
    _frac_dyn_range: Dict[float, float] = None
    _color_map: str = None
    _color_features: str = None
    _thickness_features: float = None
    _size_features_neam: float = None
    _frequency_guide: Optional[List[float]] = None
    _measurements: Optional[List[str]] = None
    _measurements_1d: Optional[List[str]] = None
    def __init__(
            self,
            dataset: DataSet, view: ViewMatPlotLib, measurements: Optional[List[str]] = None,
            log_level: Optional[int] = None
    ):
        """
        Initializes the presenter with the dataset and view it links
        :param dataset: The dataset
        :param view: The view handler
        :param measurements: The measurements to plot from the dataset
        """
        self._dataset = dataset
        self._view = view
        self._measurements = measurements
        dataset.register_presenter(self)
        view.register_presenter(self)
        if log_level:
            log.setLevel(log_level)

        log.debug("Presenter: Initialized")

    def run(self):
        """
        Runs the software
        """
        self._view.run()


    def register_feature(self, vertexes: List[Tuple[Time, float]], name: str, crop_to_bounds: bool = False) -> Feature:
        """
        Registers a new feature on the dataset.

        :param vertexes: List of vertexes in the format (julian date, frequency)
        :param name: Name of the feature
        """
        
        vertexes = Feature.cropping(vertexes, self._dataset.get_bbox(self._time_start, self._time_end))
        return self._dataset.add_feature(name=name, vertexes=vertexes)

    def request_measurements(self):
        """
        Selects the range of measurements to plot.
        """
        measurements = self._dataset.get_measurement_names()
        log.info(f"request_measurements: File contains {measurements}")
        if len(measurements) > 1:
            self._measurements = self._view.select_measurements(measurements)
        else:
            self._measurements = measurements

        log.info(f"request_measurements: Selected {self._measurements}")

    def request_save(self):
        """
        Handles requests from the view to save the current data to file.
        """
        self._dataset.write_features_to_json()
        self._dataset.write_features_to_text()

    def request_data_time_range(
            self,
            time_start: Time,
            time_end: Time,
            fig_size: Tuple[float, float],
            frac_dyn_range: Dict[float, float],
            color_map = str,
            color_features = str,
            thickness_features = float,
            size_features_name = float,
            frequency_guide: List[float] = None,
            overlap_fraction: float = OVERLAP_FRACTION
    ):
        """
        Selects the data for the given time range, and draws it on the figure.
        Adds a few days either side to render (but these are excluded when progressing forwards and back)

        :param time_start: The start of the time window
        :param time_end: The end of the time window

        """
        log.debug("request_data_time_range: Started...")
        self._time_start = time_start
        self._time_end = time_end
        self._fig_size = fig_size
        self._frac_dyn_range = frac_dyn_range
        self._frequency_guide = frequency_guide
        self._color_map = color_map
        self._color_features = color_features
        self._thickness_features = thickness_features
        self._size_features_name = size_features_name

        time, freq, data = self._dataset.get_data_for_time_range(
            time_start, time_end, measurements=self._measurements
        )
        time, data_1d = self._dataset.get_1d_data_for_time_range(
            time_start, time_end, measurements=self._measurements_1d
        )
        
        features: List[Feature] = self._dataset.get_features_for_time_range(
            time_start, time_end
        )

        self._view.draw_data(
            time, freq, data, self._dataset.get_units(), # data from the preprocessed file
            data_1d, self._frequency_guide, #optionnal 1D data from either the preprocessed file or the -g arugment
            fig_size= self._fig_size,
            frac_dyn_range=frac_dyn_range,
            color_map = self._color_map,
            color_features = self._color_features,
            thickness_features = self._thickness_features,
            size_features_name = self._size_features_name,
            features=features
        )
        
        log.debug(f"request_data_time_range: Complete")

    def request_data_next(self, overlap_fraction: float = OVERLAP_FRACTION):
        """
        Handles requests from the view to provide the next window of data.

        :param overlap_fraction: Fraction of the range to overlap with the previous window
        """
        time_window: timedelta = self._time_end - self._time_start

        self.request_data_time_range(
            time_start=self._time_start + time_window * (1.0 - overlap_fraction),
            time_end=self._time_end + time_window * (1.0 - overlap_fraction),
            fig_size=self._fig_size,
            frac_dyn_range=self._frac_dyn_range, color_map=self._color_map,
            color_features=self._color_features,
            thickness_features=self._thickness_features,
            size_features_name = self._size_features_name,
            frequency_guide=self._frequency_guide
        )
        log.debug("request_data_next: Complete")

    def request_data_prev(self, overlap_fraction: float = OVERLAP_FRACTION):
        """
        Handles requests from the view to provide the previous window of data.

        :param overlap_fraction: Fraction of the range to overlap with the previous window
        """
        time_window: timedelta = self._time_end - self._time_start

        self.request_data_time_range(
            time_start=self._time_start - time_window * (1.0 - overlap_fraction),
            time_end=self._time_end - time_window * (1.0 - overlap_fraction),
            fig_size=self._fig_size,
            frac_dyn_range=self._frac_dyn_range, color_map=self._color_map,
            color_features=self._color_features,
            thickness_features=self._thickness_features,
            size_features_name=self._size_features_name,
            frequency_guide=self._frequency_guide
        )
        log.debug("request_data_prev: Complete")


    
        