import logging

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, TYPE_CHECKING, Optional

from astropy.time import Time
from numpy import ndarray  # Imported separately for ease of Typing

from spacelabel.models.feature import Feature

if TYPE_CHECKING:
    from spacelabel.presenters import Presenter

log = logging.getLogger(__name__)

# We default to assuming measurements should be logarithmically scaled. This can be overridden here for names.
SHOULD_MEASUREMENT_BE_LOG = {
    "Degree of polarization": False
}


class View(ABC):
    """
    Abstract base class for the viewer
    """
    _presenter: 'Presenter' = None

    def __init__(self, log_level: Optional[int] = None):
        """
        Initializes the log level
        """
        if log_level:
            log.setLevel(log_level)

        log.debug("View: Initialized")

    def register_presenter(self, presenter: 'Presenter'):
        """
        Links the dataset to the presenter that manages it.
        """
        self._presenter = presenter

    @abstractmethod
    def run(self):
        """
        Abstract method for running the view.
        """
        pass

    @abstractmethod
    def select_measurements(self, measurements: List[str]) -> List[str]:
        """
        Abstract method to select the measurements they'd like shown
        """
        return []

    @abstractmethod
    def draw_data(
            self, time: Time, freq: ndarray, data: Dict[str, ndarray], units: Dict[str, str],
            data_1d: Dict[str, ndarray], frequency_guide: None,
            fig_size: Tuple[float, float],
            frac_dyn_range: Dict[float,float],
            color_map: str,
            color_features: str,
            thickness_features: float,
            size_features_name: float,
            features: Optional[List[Feature]]
    ):
        """
        Abstract method to draw the data and features provided
        """
        pass
        
    @abstractmethod
    def draw_1d_data(
            self, time: Time, data: Dict[str, ndarray],
            #units: Dict[str, str],
            frequency_guide: None, frequency_guide_units: Dict[str, str]
    ):
        """
        Abstract method to draw the 1d time series data
        """
        pass

