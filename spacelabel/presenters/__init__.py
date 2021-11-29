from datetime import datetime, timedelta
from numpy import datetime64
from typing import List, Optional, Tuple

from spacelabel.models.dataset import DataSet
from spacelabel.models.feature import Feature
from spacelabel.views import View


class Presenter:
    """

    """
    _dataset: DataSet = None
    _view: View = None
    _time_start: datetime = None
    _time_end: datetime = None
    _measurements: Optional[List[str]] = None

    def __init__(self, dataset: DataSet, view: View, measurements: Optional[List[str]] = None):
        """
        Initialises the presenter with the dataset and view it links
        :param dataset: The dataset
        :param view: The view handler
        :param measurements: The measurements to plot from the dataset
        """
        self._dataset = dataset
        self._view = view
        self._measurements = measurements
        dataset.register_presenter(self)
        view.register_presenter(self)

    def register_feature(self, vertexes: List[Tuple[datetime64, float]], name: str):
        """
        Registers a new feature on the dataset
        :param vertexes:
        :param name:
        """
        self._dataset.add_feature(name=name, vertexes=vertexes)

    def request_save(self):
        """
        Handles requests from the view to save the current data to file.
        """
        self._dataset.write_features_to_json()
        self._dataset.write_features_to_text()

    def request_data_time_range(self, time_start: datetime, time_end: datetime, days_padding: int = 3):
        """
        Selects the data for the given time range, and draws it on the figure.
        Adds a few days either side to render (but these are excluded when progressing forwards and back)
        :param time_start: The start of the time window
        :param time_end: The end of the time window
        :param days_padding: Extra days that are added either side of the time range
        """
        self._time_start = time_start
        self._time_end = time_end
        time_padding: timedelta = timedelta(days=days_padding)

        time, flux, data = self._dataset.get_data_for_time_range(
            time_start - time_padding, time_end + time_padding, measurements=self._measurements
        )
        self._view.draw_data(
            time, flux, data, self._dataset.get_units()
        )
        features: List[Feature] = self._dataset.get_features_for_time_range(
            time_start - time_padding, time_end + time_padding
        )

        self._view.draw_features(
            features=[feature.vertexes() for feature in features]
        )

    def request_data_next(self):
        """
        Handles requests from the view to provide the next window of data.
        """
        time_window: timedelta = self._time_end - self._time_start
        self.request_data_time_range(
            time_start=self._time_start + time_window,
            time_end=self._time_end + time_window
        )

    def request_data_prev(self):
        """
        Handles requests from the view to provide the previous window of data.
        """
        time_window: timedelta = self._time_end - self._time_start
        self.request_data_time_range(
            time_start=self._time_start - time_window,
            time_end=self._time_end
        )
