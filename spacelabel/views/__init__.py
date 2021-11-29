import numpy
from easygui import enterbox
from matplotlib.colors import LogNorm
from matplotlib.patches import Polygon
from matplotlib.pyplot import Figure, Axes, figure
from matplotlib.widgets import PolygonSelector, Button
from mpl_toolkits import axes_grid1
from numpy import ndarray  # Imported seperately for ease of Typing
from typing import Dict, List


FIGURE_SIZE = (15, 5)
FONT_SIZE = 12


class View:
    """

    """
    _fig: Figure = None
    _axes: Dict[str, Axes] = None
    _ax_cbar: Axes = None
    _ax_data: Axes = None
    _feature_name: str = None
    _presenter = None
    _selector: PolygonSelector = None
    _button_next: Button = None
    _button_prev: Button = None
    _button_save: Button = None

    def __init__(self):
        """
        Defines the figure and canvas
        """
        self._fig = figure(figsize=FIGURE_SIZE, constrained_layout=True)

        self._axes = self._fig.subplot_mosaic(
            """BCCCA
               DDDDD
               DDDDD
               DDDDD
               DDDDD"""
        )
        self._button_next = Button(self._axes['C'], 'Next')
        self._button_next.on_clicked(self.event_button_next)

        self._button_prev = Button(self._axes['A'], 'Prev')
        self._button_next.on_clicked(self.event_button_prev)

        self._button_save = Button(self._axes['C'], 'Save')
        self._button_save.on_clicked(self.event_button_save)

        # Shouldn't be necessary
        # self._fig.canvas.mpl_connect('key_press_event', self.event_keypress)

    def register_presenter(self, presenter):
        self._presenter = presenter

    def event_selected(self, vertexes: ndarray):
        """
        Triggered when the user finishes drawing a polygon on the plot,
        and requests a name for the finished polygon (defaulting to the last one used)
        :param vertexes: The vertexes selected on the figure
        """
        self._feature_name = enterbox(
            "Feature Selected", "Please name your feature", self._feature_name
        )
        self._presenter.register_feature(vertexes, self._feature_name)
        self._selector = PolygonSelector(
            self._axes['D'], onselect=self.event_selected
        )

    def draw_features(self, features: List[ndarray]):
        """
        Plot the provided features on the map.
        :param features:
        """
        for feature in features:
            self._axes['D'].add_patch(
                Polygon(feature, color='k', linestyle='--', linewidth=1.5, alpha=0.5, fill=False)
            )
        self._fig.show()

    def draw_data(
            self, time: ndarray, freq: ndarray, data: Dict[str, ndarray], units: Dict[str, str]
    ):
        """
        Renders a batch of data on the plot. This is for the single-data version.
        """

        meas = data[list(data.keys())[0]]

        vmin = numpy.quantile(meas[meas > 0.], 0.05)
        vmax = numpy.quantile(meas[meas > 0.], 0.95)
        norm = LogNorm(vmin=vmin, vmax=vmax)

        image = self._axes['D'].pcolormesh(time, freq, meas, cmap='Spectral_r', norm=norm, shading='auto')

        # Formatting Axes
        self._axes['D'].set_xlabel('Time', fontsize=FONT_SIZE)
        self._axes['D'].set_ylabel(f"Frequency ({units['frequency']})", fontsize=FONT_SIZE)
        # date_fmt = mdates.DateFormatter('%Y-%j\n%H:%M')
        # ax.xaxis.set_major_formatter(date_fmt)

        # Formatting colourbar
        divider = axes_grid1.make_axes_locatable(self._axes['D'])
        cax = divider.append_axes("right", size=0.15, pad=0.2)
        cb = self._fig.colorbar(
            image, extend='both', shrink=0.9, cax=cax, ax=self._axes['D']
        )
        cb.set_label(r'Intensity (V$^2$/m$^2$/Hz)', fontsize=FONT_SIZE + 2)

        self._fig.show()
        self._selector = PolygonSelector(
            self._axes['D'], onselect=self.event_selected
        )

    def event_button_next(self, event):
        """

        """
        del self._selector
        self._axes['D'].clear()
        self._presenter.request_data_next()

    def event_button_prev(self, event):
        """

        """
        del self._selector
        self._axes['D'].clear()
        self._presenter.request_data_prev()

    def event_button_save(self, event):
        """

        """
        self._presenter.request_save()