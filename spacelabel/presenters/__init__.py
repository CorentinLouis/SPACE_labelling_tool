import logging

from astropy.time import Time, TimeDelta
from datetime import datetime, timedelta
from numpy import datetime64
from typing import List, Optional, Tuple, Dict

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
    _frac_dyn_range: Dict[float, float] = None
    _measurements: Optional[List[str]] = None

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

    def register_feature(self, vertexes: List[Tuple[Time, float]], name: str) -> Feature:
        """
        Registers a new feature on the dataset.

        :param vertexes: List of vertexes in the format (julian date, frequency)
        :param name: Name of the feature
        """
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
            frac_dyn_range: Dict[float, float],
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
        self._frac_dyn_range = frac_dyn_range

        time, flux, data = self._dataset.get_data_for_time_range(
            time_start, time_end, measurements=self._measurements
        )
        features: List[Feature] = self._dataset.get_features_for_time_range(
            time_start, time_end
        )

        self._view.draw_data(
            time, flux, data, self._dataset.get_units(),
            frac_dyn_range=frac_dyn_range,
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
            frac_dyn_range=self._frac_dyn_range
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
            frac_dyn_range=self._frac_dyn_range
        )
        log.debug("request_data_prev: Complete")
