import logging
import numpy

from astropy.time import Time
from easygui import enterbox
from matplotlib.backend_bases import MouseEvent
from matplotlib.colors import LogNorm
from matplotlib.dates import num2julian
from matplotlib.pyplot import Figure, Axes, figure
from matplotlib.widgets import PolygonSelector, Button
from matplotlib.pyplot import show, close
from numpy import ndarray  # Imported separately for ease of Typing
from typing import Dict, List, Tuple, TYPE_CHECKING, Optional

from spacelabel.models.feature import Feature

if TYPE_CHECKING:
    from spacelabel.presenters import Presenter

FIGURE_SIZE: Tuple[float, float] = (15, 5)
FONT_SIZE: float = 12.0
FONT_SIZE_LARGE: float = 14.0
USE_BLIT: bool = False

log = logging.getLogger(__name__)
# ion()  # Matplotlib interactive mode on


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
    _measurements: List[str] = None

    def __init__(self, log_level: Optional[int] = None):
        """
        Defines the figure and canvas
        """
        # ion()
        # Shouldn't be necessary
        # self._fig.canvas.mpl_connect('key_press_event', self.event_keypress)
        self._create_canvas()
        if log_level:
            log.setLevel(log_level)

        log.debug("View: Initialised")

    def _create_canvas(self):
        """
        Creates the canvas for drawing on.
        Private method - should not be called by rest of MVP architecture.
        """
        log.debug("_create_canvas: Starting...")
        self._fig = figure(figsize=FIGURE_SIZE)
        self._ax_prev = self._fig.add_axes([0.01, 0.91, 0.18, 0.08])
        self._ax_save = self._fig.add_axes([0.21, 0.91, 0.58, 0.08])
        self._ax_next = self._fig.add_axes([0.81, 0.91, 0.18, 0.08])

        self._ax_cbar = self._fig.add_axes([0.87, 0.10, 0.05, 0.80])
        self._ax_data = self._fig.add_axes([0.05, 0.10, 0.80, 0.80])

        self._button_prev = Button(self._ax_prev, 'Prev')
        self._button_prev.on_clicked(self._event_button_prev)

        self._button_save = Button(self._ax_save, 'Save')
        self._button_save.on_clicked(self._event_button_save)

        self._button_next = Button(self._ax_next, 'Next')
        self._button_next.on_clicked(self._event_button_next)
        log.debug("_create_canvas: Complete")

    def _clear_canvas(self):
        """
        Clears and removes the current canvas.
        Manually removes all patches, as for some reason `close(fig)` will not.
        """
        del self._selector
        close(self._fig)
        del self._fig
        log.debug("_event_button_prev: Closed & deleted figure")

    def register_presenter(self, presenter: 'Presenter'):
        """
        Links the dataset to the presenter that manages it.
        """
        self._presenter = presenter

    def draw_data(
            self, time: Time, freq: ndarray, data: Dict[str, ndarray], units: Dict[str, str],
            features: Optional[List[Feature]]
    ):
        """
        Renders a batch of data on the plot. This is for the single-data version.
        :param time:
        :param freq:
        :param data:
        :param units:
        :param features: Features in the data time range, if any
        """
        meas: ndarray = data[list(data.keys())[0]]

        vmin: float = numpy.quantile(meas[meas > 0.], 0.05)
        vmax: float = numpy.quantile(meas[meas > 0.], 0.95)
        norm: LogNorm = LogNorm(vmin=vmin, vmax=vmax)

        # Convert the time from Astropy Time to numpy datetimes, which matplotlib can take in
        time = time.datetime64

        image = self._ax_data.pcolormesh(
            time, freq, meas,
            cmap='Spectral_r',
            norm=norm,
            shading='auto'
        )
        self._ax_data.set_xlim(time[0], time[-1])
        self._ax_data.set_ylim(freq[0], freq[-1])

        # Formatting Axes
        self._ax_data.set_xlabel('Time', fontsize=FONT_SIZE)
        self._ax_data.set_ylabel(f"Frequency ({units['frequency']})", fontsize=FONT_SIZE)

        # Formatting colour bar
        cb = self._fig.colorbar(
            image, extend='both', cax=self._ax_cbar, ax=self._ax_data
        )
        cb.set_label(r'Intensity (V$^2$/m$^2$/Hz)', fontsize=FONT_SIZE_LARGE)

        if features:
            self._draw_features(features)

        self._create_polyselector()
        self._fig.show()
        show()  # `fig.show()` doesn't work

        log.debug("draw_data: Complete")

    def _draw_features(self, features: List[Feature]):
        """
        Plot the provided features on the map.

        :param features: The list of features to draw
        """
        for feature in features:
            self._draw_fill(*feature.arrays())

        log.debug(f"_draw_features: Drawn {len(features)}")

    def _draw_fill(self, time: Time, frequency: ndarray):
        """
        Plot a single feature on the map.

        :param time:
        :param frequency:
        """
        time_datetime = time.datetime64

        self._ax_data.fill(
            time_datetime, frequency,
            edgecolor='k',
            linestyle='--', linewidth=1.5,
            alpha=0.75, fill=False
        )

    def _create_polyselector(self):
        """
        Generates a new polygon selector
        """
        if self._selector:
            del self._selector

        self._selector = PolygonSelector(
            self._ax_data, onselect=self._event_selected, useblit=USE_BLIT,
            lineprops={
                'color': 'k', 'linestyle': '--', 'linewidth': 1.5, 'alpha': 0.75
            }
        )
        log.debug("_create_polyselector: Complete")

    def _event_button_next(self, event: MouseEvent):
        """
        Triggered when the user clicks the 'Next' button.
        """
        self._clear_canvas()
        self._create_canvas()
        self._presenter.request_data_next()

    def _event_button_prev(self, event: MouseEvent):
        """
        Triggered when the user clicks the 'Previous' button.
        """
        self._clear_canvas()
        self._create_canvas()
        self._presenter.request_data_prev()

    def _event_button_save(self, event: MouseEvent):
        """
        Triggered when the user clicks the 'Save' button.
        """
        self._presenter.request_save()
        log.debug("_event_button_save: Complete")

    def _event_selected(self, vertexes: List[Tuple[float, float]]):
        """
        Triggered when the user finishes drawing a polygon on the plot,
        and requests a name for the finished polygon (defaulting to the last one used)
        :param vertexes: The vertexes selected on the figure. Annoyingly, uses internal MatLab time.
        """
        self._feature_name = enterbox(
            "Feature Selected", "Please name your feature", self._feature_name
        )

        if self._feature_name:
            vertexes_jd_format: List[Tuple[Time, float]] = [
                (
                    Time(num2julian(vertex[0]), format='jd'),
                    vertex[1]
                ) for vertex in vertexes
            ]
            feature: Feature = self._presenter.register_feature(vertexes_jd_format, self._feature_name)

            if USE_BLIT:
                # We re-plot the one we just took - only necessary for blit mode
                self._draw_fill(feature.arrays())

        log.info(f"_event_selected: New feature '{self._feature_name}'")
        self._create_polyselector()
