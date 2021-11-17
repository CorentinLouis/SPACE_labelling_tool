from os import remove

import numpy as np
from matplotlib import dates as mdates, pyplot as plt, colors as colors
from matplotlib.patches import Polygon
from matplotlib.widgets import PolygonSelector

from datetime import datetime, timedelta

from mpl_toolkits import axes_grid1

from spacelabel.io import write_file, open_and_draw, extract_data

from typing import Optional


class Poly:  # class to make each polygon shape

    def __init__(self, ax, fig, view_date_start, view_date_end, file_data):  # initialising
        self.canvas = ax.figure.canvas
        self.ax = ax
        self.fig = fig
        props = dict(color='k', linestyle='--', linewidth=1.5, alpha=0.75)
        self.polygon = PolygonSelector(ax, self.on_select, useblit=False, lineprops=props)
        self.vertices = []
        self.shapes = []
        self.name = None
        self.date_end: Optional[datetime] = None
        self.date_start: Optional[datetime] = None
        self.view_date_start: datetime = view_date_start
        self.view_date_end: datetime = view_date_end
        self.file_data = file_data
        self.keypress_callback = None

    # function that deals with the vertices of each polygon when selected

    def on_select(self, verts):
        print("Selected a polygon...")
        self.vertices = verts
        self.date_end = mdates.num2date(max(np.array(self.vertices)[:, 0]))
        self.date_start = mdates.num2date(min(np.array(self.vertices)[:, 0]))

    def new_name(self):
        n = input('\n Feature Label: ')
        self.name = n

    def new_poly(self, event):
        if event.key == 'enter':
            print("New polygon being generated...")
            a = Poly(self.ax, self.on_select, self.view_date_start, self.view_date_end, self.file_data)
            a.new_name()
            self.shapes.append(a)
            plt.draw()

        if event.key == 'q':
            plt.close(self.fig)
            try:
                self.date_end = mdates.num2date(max(np.array(self.vertices)[:, 0]))
                self.date_start = mdates.num2date(min(np.array(self.vertices)[:, 0]))
                self.shapes.insert(0, self)
                write_file(self.shapes, self.file_data['units'], self.file_data['obs'])
                print('\n Polygon data saved to file...')

            except IndexError:
                print('\n No new polygons to save to file...')

        if event.key == 'escape':
            self.shapes.clear()
            self.vertices.clear()

        if event.key == 'r':
            rename = input('\n Enter new feature label: ')
            self.name = rename

        if event.key == 'right' or event.key == 'left':
            print(f"Moving {event.key}")
            try:
                print(f"Saving to file...")
                self.date_end = mdates.num2date(max(np.array(self.vertices)[:, 0]))
                self.date_start = mdates.num2date(min(np.array(self.vertices)[:, 0]))
                self.shapes.insert(0, self)
                write_file(self.shapes, self.file_data['units'], self.file_data['obs'])
                print('\n Polygon data saved to file.')

            except IndexError:
                print('\n No new polygons to save to file...')

            time_diff: timedelta = self.view_date_end - self.view_date_start

            if event.key == 'right':
                direction = 'forward'
                view_date_start = self.view_date_start + time_diff - timedelta(days=3)
                view_date_end = self.view_date_end + time_diff + timedelta(days=3)
            else:  # If left
                direction = 'backward'
                view_date_start = self.view_date_start - time_diff - timedelta(days=3)
                view_date_end = self.view_date_end - time_diff + timedelta(days=3)

            if self.keypress_callback:
                self.canvas.mpl_disconnect(self.keypress_callback)

            plt.close(self.fig)

            # TODO: This was supposed to stop the user from scrolling out of scope of the file, we need to duplicate that
            # if float(str(view_date_end)[-3:]) >= 350 or float(str(view_date_start)[-3:]) <= 15:
            #     view_date_start = datetime.fromisoformat(input('\n Please enter your start day (YYYY-DD-MM): '))
            #     view_date_end = datetime.fromisoformat(input('\n Please enter your end day (YYYY-DD-MM): '))
            #     saved_polys = open_and_draw(view_date_start, view_date_end)
            #     plot_and_interact(view_date_start, view_date_end, file_data, colour_in=saved_polys, fwd=direction)
            # else:
            saved_polys = open_and_draw(view_date_start, view_date_end)
            plot_and_interact(view_date_start, view_date_end, self.file_data, colour_in=saved_polys, fwd=direction)

        else:
            return None


# The setting up and interacting with the plots using polygonSelector
def plot_and_interact(date_start, date_end, file, colour_in=None, fwd=None, again=False):

    time, freq, flux = extract_data(file, date_start=date_start, date_end=date_end)

    figsize = (15, 5)

    fontsize = 12

    vmin = np.quantile(flux[flux > 0.], 0.05)
    vmax = np.quantile(flux[flux > 0.], 0.95)
    scaleZ = colors.LogNorm(vmin=vmin, vmax=vmax)

    # First plot the data as pcolormesh object and save it as a .png
    fig1, ax1 = plt.subplots(figsize=figsize, constrained_layout=True)
    im1 = ax1.pcolormesh(time, freq, flux, cmap='Spectral_r', norm=scaleZ, shading='auto')

    ax1.set_axis_off()
    plt.savefig('radioSpectra.png', bbox_inches='tight', pad_inches=0)
    plt.close(fig1)
    # Open the image and load into graph to save memory
    image = plt.imread('radioSpectra.png')
    remove('radioSpectra.png')
    fig2, ax2 = plt.subplots(figsize=figsize, sharex='all', sharey='all')
    ax2.set_yscale('log')
    mt = mdates.date2num((min(time), max(time)))

    # Formatting Axes
    ax2.set_xlabel('Time', fontsize=fontsize)
    ax2.set_ylabel(f'Frequency ({file["units"]})', fontsize=fontsize)
    ax2.set_title(f'{file["obs"]} Data - {date_start} to {date_end}', fontsize=fontsize + 2)
    dateFmt = mdates.DateFormatter('%Y-%M-%D\n%H:%M')
    ax2.xaxis.set_major_formatter(dateFmt)

    # Formatting colourbar
    figure = ax2.figure
    divider = axes_grid1.make_axes_locatable(ax2)
    cax = divider.append_axes("right", size=0.15, pad=0.2)
    cb = figure.colorbar(im1, extend='both', shrink=0.9, cax=cax, ax=ax2)
    cb.set_label(r'Intensity (V$^2$/m$^2$/Hz)', fontsize=fontsize+2)

    if colour_in:
        for shape in colour_in:
            ax2.add_patch(Polygon(shape, color='k', linestyle='--', linewidth=1.5, alpha=0.75, fill=False))

    ax2.imshow(image, aspect='auto', extent=[mt[0], mt[1], min(freq), max(freq)])

    # Plotting and interacting
    # Begins by basic instruction

    if again:

        print('Begin by inputting a name for the feature. ')
        ply1 = Poly(ax2, fig2, date_start, date_end, file)  # Start drawing a polygon
        ply1.name = input('\n Feature label: ')

        print('\n Select the vertices of your polygon with your mouse, complete the shape by clicking on the starting point. \n Edit the shape by drag and dropping any of the vertices on your polygon.')
        print('\n To start a new polygon press enter before providing it with a name. When done, simply press "q" ')
    else:
        ply1 = Poly(ax2, fig2, date_start, date_end, file)  # Start drawing a polygon
        ply1.name = input('\n Feature label: ')

    ply1.keypress_callback = fig2.canvas.mpl_connect('key_press_event', ply1.new_poly)
    plt.ion()
    plt.show(block=True)
