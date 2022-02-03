import logging
import numpy

from astropy.time import Time
from astropy.visualization import time_support
from easygui import enterbox
from matplotlib.backend_bases import MouseEvent
from matplotlib.colors import LogNorm
from matplotlib.patches import Polygon
from matplotlib.pyplot import Figure, Axes, figure
from matplotlib.widgets import PolygonSelector, Button
from matplotlib.pyplot import show, ion
from mpl_toolkits import axes_grid1
from numpy import ndarray, datetime64  # Imported separately for ease of Typing
from typing import Dict, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from spacelabel.presenters import Presenter

FIGURE_SIZE: Tuple[float, float] = (15, 5)
FONT_SIZE: float = 12


log = logging.getLogger(__name__)


class View:
    """
    Class that handles the presentation of data in a single matplotlib figure and user interactions with it.
    """
    _fig: Figure = None
    _axes: Dict[str, Axes] = None
    _ax_cbar: Axes = None
    _ax_data: Axes = None
    _ax_prev: Axes = None
    _ax_next: Axes = None
    _ax_save: Axes = None
    _feature_name: str = None
    _presenter: 'Presenter' = None
    _selector: PolygonSelector = None
    _button_next: Button = None
    _button_prev: Button = None
    _button_save: Button = None

    def __init__(self):
        """
        Defines the figure and canvas
        """
        self._fig = figure(figsize=FIGURE_SIZE)
        self._ax_prev = self._fig.add_axes([0.01, 0.91, 0.18, 0.08])
        self._ax_save = self._fig.add_axes([0.21, 0.91, 0.58, 0.08])
        self._ax_next = self._fig.add_axes([0.81, 0.91, 0.18, 0.08])

        self._ax_cbar = self._fig.add_axes([0.87, 0.10, 0.05, 0.80])
        self._ax_data = self._fig.add_axes([0.05, 0.10, 0.80, 0.80])

        self._button_prev = Button(self._ax_prev, 'Prev')
        self._button_prev.on_clicked(self.event_button_prev)

        self._button_save = Button(self._ax_save, 'Save')
        self._button_save.on_clicked(self.event_button_save)

        self._button_next = Button(self._ax_next, 'Next')
        self._button_next.on_clicked(self.event_button_next)

        log.info("Initialised canvas")

        # ion()
        # Shouldn't be necessary
        # self._fig.canvas.mpl_connect('key_press_event', self.event_keypress)

    def register_presenter(self, presenter: 'Presenter'):
        """Links the dataset to the presenter that manages it."""
        self._presenter = presenter

    def event_selected(self, vertexes: List[Tuple[float, float]]):
        """
        Triggered when the user finishes drawing a polygon on the plot,
        and requests a name for the finished polygon (defaulting to the last one used)
        :param vertexes: The vertexes selected on the figure. Annoyingly, uses internal MatLab time.
        """
        self._feature_name = enterbox(
            "Feature Selected", "Please name your feature", self._feature_name
        )
        self._presenter.register_feature(vertexes, self._feature_name)

        # We re-plot the one we just took
        self.draw_polygon(vertexes)

        self._selector = PolygonSelector(
            self._ax_data, onselect=self.event_selected, useblit=True
        )

    def draw_features(self, features: List[List[Tuple[datetime64, float]]]):
        """
        Plot the provided features on the map.
        :param features: The list of features, each of which is a list of tuples of time-frequency points.
        """
        for feature in features:
            self.draw_polygon(feature)

        log.info(f"Drawn {len(features)} features")

    def draw_polygon(self, vertexes: List[Tuple[datetime64, float]]):
        """
        Plot a single feature on the map.
        :param vertexes: The vertexes of a single feature
        """
        self._ax_data.add_patch(
            Polygon(vertexes, color='k', linestyle='--', linewidth=1.5, alpha=0.5, fill=False)
        )

    def draw_data(
            self, time: Time, freq: ndarray, data: Dict[str, ndarray], units: Dict[str, str]
    ):
        """
        Renders a batch of data on the plot. This is for the single-data version.
        :param time:
        :param freq:
        :param data:
        :param units:
        """

        meas: ndarray = data[list(data.keys())[0]]

        vmin: float = numpy.quantile(meas[meas > 0.], 0.05)
        vmax: float = numpy.quantile(meas[meas > 0.], 0.95)
        norm: LogNorm = LogNorm(vmin=vmin, vmax=vmax)

        # Need to enable support for Astropy time units
        time = time.datetime64
        image = self._ax_data.pcolormesh(
            time, freq, meas, cmap='Spectral_r', norm=norm, shading='auto'
        )
        self._ax_data.set_xlim(time[0], time[-1])
        log.info("Drawn image")

        # Formatting Axes
        self._ax_data.set_xlabel('Time', fontsize=FONT_SIZE)
        self._ax_data.set_ylabel(f"Frequency ({units['frequency']})", fontsize=FONT_SIZE)
        log.info("Drawn axes")

        # Formatting colourbar
        cb = self._fig.colorbar(
            image, extend='both', cax=self._ax_cbar, ax=self._ax_data
        )
        cb.set_label(r'Intensity (V$^2$/m$^2$/Hz)', fontsize=FONT_SIZE + 2)

        self._selector = PolygonSelector(
            self._ax_data, onselect=self.event_selected, useblit=True,
            lineprops={
                'color': 'k', 'linestyle': '--', 'linewidth': 1.5, 'alpha': 0.75
            }
        )
        log.info("Drawn data")
        self._fig.show()
        show()

    def event_button_next(self, event: MouseEvent):
        """Triggered when the user clicks the 'Next' button."""
        del self._selector
        self._ax_data.clear()
        self._ax_cbar.clear()
        self._presenter.request_data_next()

    def event_button_prev(self, event: MouseEvent):
        """Triggered when the user clicks the 'Previous' button."""
        del self._selector
        self._ax_data.clear()
        self._ax_cbar.clear()
        self._presenter.request_data_prev()

    def event_button_save(self, event: MouseEvent):
        """Triggered when the user clicks the 'Save' button."""
        self._presenter.request_save()
