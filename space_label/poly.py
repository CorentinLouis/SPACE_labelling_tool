import numpy as np
from matplotlib import dates as mdates, pyplot as plt
from matplotlib.widgets import PolygonSelector

from datetime import datetime, timedelta
from space_develop import file_data, plot_and_interact
from space_label.io import write_file, open_and_draw


class Poly:  # class to make each polygon shape

    def __init__(self, ax, fig, start_day, end_day, file_data):  # initialising
        self.canvas = ax.figure.canvas
        self.ax = ax
        self.fig = fig
        props = dict(color='k', linestyle='--', linewidth=1.5, alpha=0.75)
        self.polygon = PolygonSelector(ax, self.on_select, useblit=False, lineprops=props)
        self.vertices = []
        self.shapes = []
        self.name = None
        self.end = None
        self.start = None
        self.start_day = start_day
        self.end_day = end_day
        self.file_data = file_data

    # function that deals with the vertices of each polygon when selected

    def on_select(self, verts):
        self.vertices = verts
        self.end = float(mdates.num2date(max(np.array(self.vertices)[:, 0])).strftime('%Y%j.%H'))
        self.start = float(mdates.num2date(min(np.array(self.vertices)[:, 0])).strftime('%Y%j.%H'))

    def new_name(self):
        n = input('\n Feature Label: ')
        self.name = n

    def new_poly(self, event):
        if event.key == 'enter':
            a = Poly(self.ax, self.on_select, self.start_day, self.end_day, self.file_data)
            a.new_name()
            self.shapes.append(a)
            plt.draw()

        if event.key == 'q':
            plt.close(self.fig)
            try:
                self.end = float(mdates.num2date(max(np.array(self.vertices)[:, 0])).strftime('%Y%j.%H'))
                self.start = float(mdates.num2date(min(np.array(self.vertices)[:, 0])).strftime('%Y%j.%H'))
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
            try:
                self.end = float(mdates.num2date(max(np.array(self.vertices)[:, 0])).strftime('%Y%j.%H'))
                self.start = float(mdates.num2date(min(np.array(self.vertices)[:, 0])).strftime('%Y%j.%H'))
                self.shapes.insert(0, self)
                write_file(self.shapes, file_data['units'], file_data['obs'])
                print('\n Polygon data saved to file...')

            except IndexError:
                print('\n No new polygons to save to file...')

            direction = None
            time_diff = int(self.end_day-self.start_day)
            strt = None
            end = None
            if event.key == 'right':
                direction = 'forward'
                strt = self.start_day+time_diff
                end = self.end_day+time_diff
            elif event.key == 'left':
                direction = 'backward'
                strt = self.start_day-time_diff
                end = self.end_day-time_diff

            plt.close(self.fig)

            if float(str(end)[-3:]) >= 350 or float(str(strt)[-3:]) <= 15:
                strt = int(input('\n Please enter your start day (yyyydoy): '))
                end = int(input('\n Please enter your end day (yyyydoy): '))
                saved_polys = open_and_draw(strt, end)
                plot_and_interact(strt, end, file_data, colour_in=saved_polys, fwd=direction)
            else:
                saved_polys = open_and_draw(strt, end)
                plot_and_interact(strt, end, file_data, colour_in=saved_polys, fwd=direction)

        else:
            return None

