import logging
import platform
import textwrap
from typing import Tuple, Dict, Optional, List

import matplotlib
import numpy

from astropy.time import Time
from astropy.time import Time as astropyTime
from easygui import multchoicebox, enterbox
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent
from matplotlib.colors import LogNorm
from matplotlib.dates import DateFormatter, num2julian
from matplotlib.figure import Figure
from matplotlib.pyplot import ion, figure, close, pause, show, plot, axes
from matplotlib.widgets import PolygonSelector, Button, CheckButtons
from numpy import ndarray
import matplotlib.patheffects as PathEffects
from spacelabel.models.feature import Feature
from spacelabel.views import View, SHOULD_MEASUREMENT_BE_LOG

log = logging.getLogger(__name__)

#FIGURE_SIZE: Tuple[float, float] = (15, 9)
FONT_SIZE: float = 12.0
FONT_SIZE_LARGE: float = 14.0
USE_BLIT: bool = False  # When true, we get 1-5 second delays between *any* action


class ViewMatPlotLib(View):
    """
    Class that handles the presentation of data in a single matplotlib figure and user interactions with it.
    """
    _fig: Figure = None
    _fig_size: Tuple[float,float] = None
    _measurement_bottom: str = None  # Important for axis labels
    _measurement_middle: str = None  # Important for axis labels
    _ax_cbar: Dict[str, Axes] = None
    _ax_data: Dict[str, Axes] = None
    _ax_1d: Axes = None
    _ax_prev: Axes = None
    _ax_next: Axes = None
    _ax_save: Axes = None
    _feature_name: str = None
    _color_features: str = None
    _thickness_features: float = None
    _size_features_name: float = None
    _selector: Dict[str, PolygonSelector] = None
    _button_next: Button = None
    _button_prev: Button = None
    _button_save: Button = None
    _button_1d: Button = None
    _lines: List[plot] = None
    _labels: List[str] = None       


    def __init__(self, log_level: Optional[int] = None):
        """
        Defines the figure and canvas
        """
        super().__init__(log_level)
        if log_level:
            log.setLevel(log_level)

        ion()  # We want interactive MatPlotLib mode

        # Try to fix backend issues
        if platform.system() == 'Windows':
            matplotlib.use('Qt5Agg')
#        elif platform.system() == 'Darwin':
        else:
            matplotlib.use('TkAgg')

        log.debug("ViewMatPlotLib: Initialised")

    def _create_canvas(self, measurements: List[str]):
        """
        Creates the canvas for drawing on.
        Private method - should not be called by rest of MVP architecture.

        :param measurements: Names of the measurements this canvas will hold
        """
        log.debug("_create_canvas: Starting...")

        #self._fig = figure(figsize=FIGURE_SIZE)
        self._fig = figure(figsize=self._fig_size)
        self._ax_prev = self._fig.add_axes([0.01, 0.91, 0.18, 0.08])
        self._ax_save = self._fig.add_axes([0.21, 0.91, 0.58, 0.08])
        self._ax_next = self._fig.add_axes([0.81, 0.91, 0.18, 0.08])

        # We want to add a single axis per measurement
        self._ax_data_bottom = None
        self._ax_data = {}
        self._ax_cbar = {}
        height_per_measurement = 0.80 / len(measurements)
        for idx, measurement in enumerate(measurements):
            self._ax_cbar[measurement] = self._fig.add_axes(
                [
                    0.87, 0.10 + idx * height_per_measurement,  # Start location
                    0.05, height_per_measurement   # Size
                ]
            )
            self._ax_data[measurement] = self._fig.add_axes(
                [
                    0.05, 0.10 + idx * height_per_measurement,  # Start location
                    0.80, height_per_measurement,  # Size
                ],
                sharex=(None if idx == 0 else self._ax_data_bottom)
            )

            # We need to know the bottom and middle axes for axis label/tic purposes
            if idx == 0:
                log.debug(f"_create_canvas: Lowest axis is '{measurement}'")
                self._measurement_bottom = measurement

            if idx == int(len(measurements)/2):
                log.debug(f"_create_canvas: Middle axis is '{measurement}'")
                self._measurement_middle = measurement

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

    def run(self):
        """
        Run the interactive view
        """
        pause(-1)

    def select_measurements(self, measurements: List[str]) -> List[str]:
        """
        Asks the user to select the measurements they'd like shown
        """
        return multchoicebox(
            "Please select the measurements to display",
            choices=measurements
        )

    def draw_1d_data(self, time: Time, data: Dict[str, ndarray],
                     panels: None,
                     #units: Optional[Dict[str, str]],
                     frequency_guide: None, frequency_guide_units: Dict[str,str]
    ):
      
        # initiating the lines, labels and set_visible that will be necessary to create the buttons
        lines = []
        labels = []
        set_visible = []


        for i_panel in panels:
            for name, measurement in data.items():
                if i_panel == panels[0]:
                    labels.append(name)
                    set_visible.append(True)

                p = self._ax_data[i_panel].plot(time, measurement, color = "white", linestyle = "dashed")
                lines.append(p)
        
        if frequency_guide:
            for i_panel in panels:
                for value in frequency_guide:
                    # To have only one button per element in frequency_guide,
                    # no matter how many panels there are,
                    # we want to be able to count the number of panels
                    if i_panel == panels[0]:
                        labels.append(str(value)+" "+frequency_guide_units["Frequency"])
                        set_visible.append(True)
                
                    p = self._ax_data[i_panel].plot(time, numpy.repeat(float(value), len(time)), color = "white", linestyle = "dashed", visible=True)
                    lines.append(p)

        self._labels = labels
        set_visible = set_visible
        self._lines = numpy.reshape(lines, -1)


                    
        
                
        # xposition, yposition, width and height
        self._ax_1d = self._fig.add_axes([0.85, 0.0, 0.2, 0.1])
        self._button_1d = CheckButtons(self._ax_1d, labels, set_visible)
        self._button_1d.on_clicked(self._event_button_1d)


    def _event_button_1d(self, event: MouseEvent):
        n_panels = int(len(self._ax_data))
        n_labels = int(len(self._labels))
        index = self._labels.index(event)

        #self._lines[int(index)].set_visible(not self._lines[int(index)].get_visible())
        for ind_panels in range(0,n_panels):
            self._lines[int(index+ind_panels*n_labels)].set_visible(not self._lines[int(index+ind_panels*n_labels)].get_visible())


    def draw_data(
            self, time: Time, freq: ndarray, data: Dict[str, ndarray], units: Dict[str, str],
            data_1d: Dict[str, ndarray], frequency_guide: None,
            fig_size: Tuple[float, float],
            frac_dyn_range: Dict[float,float], color_map: str,
            color_features: str,
            thickness_features: float,
            size_features_name: float,
            features: Optional[List[Feature]]
    ):
        """
        Renders a batch of data on the plot.
        :param time:
        :param freq:
        :param data:
        :param units:
        :param features: Features in the data time range, if any
        """
        self._fig_size = fig_size
        self._create_canvas(list(data.keys()), )


        self._color_features = color_features
        self._thickness_features = thickness_features
        self._size_features_name = size_features_name

        # Convert the time from Astropy Time to numpy datetimes, which matplotlib can take in
        time = time.datetime64
        
        for measurement, values in data.items():
            if not SHOULD_MEASUREMENT_BE_LOG.get(measurement, True):
                norm: Optional[LogNorm] = None
            else:
                vmin: float = numpy.quantile(values[values > 0.], frac_dyn_range[0])
                vmax: float = numpy.quantile(values[values > 0.], frac_dyn_range[-1])
                norm: Optional[LogNorm] = LogNorm(vmin=vmin, vmax=vmax)
            

            image = self._ax_data[measurement].pcolormesh(
                # Clip to avoid white spots, transpose as data is time-major not frequency-major
                time, freq, values.clip(min=1e-31).T if SHOULD_MEASUREMENT_BE_LOG.get(measurement, True) else values.T,
                cmap=color_map if SHOULD_MEASUREMENT_BE_LOG.get(measurement, True) else 'coolwarm',
                norm=norm,
                shading='auto'
            )
            

            self._ax_data[measurement].set_xlim(time[0], time[-1])
            self._ax_data[measurement].set_ylim(freq[0]-0.1*freq[0], freq[-1]+0.1*freq[-1]) # Frequency limits enlarge, to be able to draw polygon on the edge of the plotting window
            self._ax_data[measurement].set_yscale('log')

            # Formatting Axes
            if measurement == self._measurement_bottom:
                self._ax_data[measurement].xaxis.set_major_formatter(
                    DateFormatter('%Y-%m-%d\n%H:%M')
                )

            else:
                self._ax_data[measurement].set_xticklabels([])

            if measurement == self._measurement_middle:
                self._ax_data[measurement].set_ylabel(
                    fr"Frequency"+(fr" (${units['Frequency']}$)" if units['Frequency'] else ""),
                    fontsize=FONT_SIZE
                )

            # Formatting colour bar
            cb = self._fig.colorbar(
                image,
                extend='both' if SHOULD_MEASUREMENT_BE_LOG.get(measurement, True) else None,  # We extend the log scale, but not linear
                cax=self._ax_cbar[measurement],
                ax=self._ax_data[measurement]
            )

            # Add on the units if there are any, then text wrap to 18-character lines
            cb.set_label(
                "\n".join(
                    textwrap.wrap(
                        fr"{measurement}",
                        width=18
                    )
                ) + ("\n"+fr"(${units[measurement]}$)" if units[measurement] else ""),
                fontsize=FONT_SIZE
            )
        
        self.draw_1d_data(
                time, 
                data_1d,
                list(data.keys()),
                frequency_guide,
                units
            )

        if features:
            self._draw_features(features, color_features, thickness_features, size_features_name)

        self._create_polyselector(color_features)
        # self._fig.show()
        show()  # `fig.show()` doesn't work

        log.debug(f"draw_data: Complete [{len(freq)}x{len(time)}]")

    def _draw_features(self, features: List[Feature],color_features: str, thickness_features:float, size_features_name: float):
        """
        Plot the provided features on the map.

        :param features: The list of features to draw
        """

        for feature in features:
            self._draw_fill(*feature.arrays(), feature._name, color_features, thickness_features, size_features_name)

        log.debug(f"_draw_features: Drawn {len(features)}")

    def _draw_fill(self, time: Time, frequency: ndarray, name: str, color_features: str, thickness_features:float, size_features_name: float):
        """
        Plot a single feature on the map.

        :param time:
        :param frequency:
        """
        time_mean = astropyTime(numpy.mean(time.value),format='jd').datetime64
        frequency_mean = numpy.mean(frequency)
        time_datetime = time.datetime64

        for axis in self._ax_data.values():
            axis.fill(
                time_datetime, frequency,

                edgecolor=color_features,
                linestyle='--', linewidth=thickness_features,
                alpha=0.75, fill=False
            )
            txt = axis.text(time_mean, frequency_mean, name, color = color_features, fontfamily = 'sans-serif', size=size_features_name)
            #txt.set_path_effects([PathEffects.withStroke(linewidth=1.25, foreground='k'),
            #           PathEffects.Normal()])

    def _create_polyselector(self, color_features: str):
        """
        Generates a new polygon selector
        """
        if self._selector:
            for selector in self._selector:
                del selector

        self._selector = {}

        for measurement, axis in self._ax_data.items():
            self._selector[measurement] = PolygonSelector(
                axis, onselect=self._event_selected, useblit=USE_BLIT,
                lineprops={
                    'color': color_features, 'linestyle': '--', 'linewidth': 1.5, 'alpha': 0.75
                }
            )
        log.debug("_create_polyselector: Complete")

    def _event_button_next(self, event: MouseEvent):
        """
        Triggered when the user clicks the 'Next' button.
        """
        self._clear_canvas()
        self._presenter.request_data_next()

    def _event_button_prev(self, event: MouseEvent):
        """
        Triggered when the user clicks the 'Previous' button.
        """
        self._clear_canvas()
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

            feature: Feature = self._presenter.register_feature(vertexes_jd_format, self._feature_name, crop_to_bounds = True)
            self._draw_fill(*feature.arrays(), feature._name, self._color_features, self._thickness_features, self._size_features_name) # Make sure the feature is drawn on all other panels of the plot

            log.info(f"_event_selected: New feature '{self._feature_name}'")

        self._create_polyselector(self._color_features)
