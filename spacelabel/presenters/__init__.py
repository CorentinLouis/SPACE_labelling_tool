from datetime import datetime
from numpy import ndarray

from spacelabel.models.dataset import DataSet
from spacelabel.views import View


class Presenter:
    """

    """
    _dataset: DataSet = None
    _view: View = None
    _time_start: datetime = None
    _time_end: datetime = None

    def __init__(self, dataset: DataSet, view: View):
        """
        Initialises the presenter with the dataset and view it links
        :param dataset:
        :param view:
        """
        self._dataset = dataset
        self._view = view
        dataset.register_presenter(self)
        view.register_presenter(self)

    def register_feature(self, vertexes: ndarray, name: str):
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

    def request_data_time_range(self, time_start: datetime, time_end: datetime):
        """
        Selects the data for the given time range, and draws it on the figure.
        :param time_start:
        :param time_end:
        """
        self._time_start = time_start
        self._time_end = time_end

        time, flux, data = self._dataset.get_data_for_time_range(
            self._time_start, self._time_end
        )
        self._view.draw_data(
            time, flux, data, self._dataset.get_units()
        )

    def request_data_next(self):
        """
        Handles requests from the view to provide the next window of data.
        """
        self._time_start = self._time_start  # TODO: Move window
        self._time_end = self._time_end
        self.request_data_time_range(
            time_start=self._time_start,
            time_end=self._time_end
        )

    def request_data_prev(self):
        """
        Handles requests from the view to provide the previous window of data.
        """
        self._time_start = self._time_start # TODO: Move window
        self._time_end = self._time_end
        self.request_data_time_range(
            time_start=self._time_start,
            time_end=self._time_end
        )
