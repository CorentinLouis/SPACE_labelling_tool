import numpy as np
from scipy.io import readsav
import datetime
from os import path, remove, environ
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits import axes_grid1
import matplotlib.colors as colors
from matplotlib.widgets import PolygonSelector
from matplotlib.patches import Polygon
import json
import time as t
import platform
from shapely.geometry import LinearRing

from datetime import timedelta



if any('SPYDER' in name for name in environ):
    if platform.system() == 'Windows':
        matplotlib.use('Qt5Agg')
    elif platform.system() == 'Darwin':
        matplotlib.use('MacOSX') 

else:
    pass

plt.ion()

# If running in the terminal setting useblit=True in line 37 will dramatically increase the interactivity speed
# of STACIE. However, in doing so once a previously drawn polygon's shape is adjusted all subsequent polygons
# will temporarily disappear until either a new polygon is drawn (hiting "enter") or the figure is closed and reopened
class Poly:  # class to make each polygon shape

    def __init__(self, ax, fig, time_view_start, time_view_end, file_data):  # initialising
        self.canvas = ax.figure.canvas
        self.ax = ax
        self.fig = fig
        props = dict(color='k', linestyle='--', linewidth=1.5, alpha=0.75)
        self.polygon = PolygonSelector(ax, self.on_select, useblit=False, lineprops=props)
        self.vertices = []
        self.shapes = []
        self.name = None
        self.time_poly_end = None
        self.time_poly_start = None
        self.time_view_start = time_view_start
        self.time_view_end = time_view_end
        self.file_data = file_data

    # function that deals with the vertices of each polygon when selected

    def on_select(self, verts):
        self.vertices = verts
        self.time_poly_end = float(mdates.num2date(max(np.array(self.vertices)[:, 0])).strftime('%Y%j.%H'))
        self.time_poly_start = float(mdates.num2date(min(np.array(self.vertices)[:, 0])).strftime('%Y%j.%H'))

    def new_name(self):
        n = input('\n Feature Label: ')
        self.name = n

    def new_poly(self, event):
        if event.key == 'enter':
            a = Poly(self.ax, self.on_select, self.time_view_start, self.time_view_end, self.file_data)
            a.new_name()
            self.shapes.append(a)
            plt.draw()

        if event.key == 'q':
            plt.close(self.fig)
            try:
                self.time_poly_end = mdates.num2date(max(np.array(self.vertices)[:, 0]))
                self.time_poly_start = mdates.num2date(min(np.array(self.vertices)[:, 0]))
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
                self.time_poly_end = mdates.num2date(max(np.array(self.vertices)[:, 0]))
                self.time_poly_start = mdates.num2date(min(np.array(self.vertices)[:, 0]))
                self.shapes.insert(0, self)
                write_file(self.shapes, self.file_data['units'], self.file_data['obs'])
                print('\n Polygon data saved to file...')

            except IndexError:
                print('\n No new polygons to save to file...')

            direction = None
            time_diff = self.time_view_end - self.time_view_start
            time_view_new_start = None
            time_view_new_end = None
            if event.key == 'right':
                direction = 'forward'
                time_view_new_start = self.time_view_start + time_diff
                time_view_new_end = self.time_view_end + time_diff
            elif event.key == 'left':
                direction = 'backward'
                time_view_new_start = self.time_view_start - time_diff
                time_view_new_end = self.time_view_end - time_diff

            plt.close(self.fig)

            # if float(str(time_view_new_end)[-3:]) >= 350 or float(str(time_view_new_start)[-3:]) <= 15:
            #     time_view_new_start = int(input('\n Please enter your start day (yyyydoy): '))
            #     time_view_new_end = int(input('\n Please enter your time_view_new_end day (yyyydoy): '))
            #     saved_polys = open_and_draw(time_view_new_start, time_view_new_end)
            #     plot_and_interact(time_view_new_start, time_view_new_end, file_data, colour_in=saved_polys, fwd=direction)
            # else:
            saved_polys = open_and_draw(time_view_new_start, time_view_new_end)
            plot_and_interact(
                time_view_new_start, time_view_new_end, self.file_data, colour_in=saved_polys, fwd=direction
            )

        else:
            return None


# All of this is dealing with the data and plotting the spectrum
def doy_to_yyyyddd(doy, origin):  # Function to change doy format to yyyyddd

    aa = np.arange(61, dtype=float)+origin  # array of years starting from 2004
    deb = np.zeros([61], dtype=float)  # zeros
    for i in range(1, len(deb)):  # categorising start point for each year
        if i % 4 == 1:
            deb[i:] = deb[i:]+366.
        else:
            deb[i:] = deb[i:]+365.

    yyyyddd = np.zeros(len(doy), dtype=float)

    for i in range(0, len(doy)):
        j = doy[i]-deb
        yyyyddd[i] = (aa[j >= 1][-1])*1000.+j[j >= 1][-1]

    return yyyyddd


# convert from doy format to datetime objects
def doy_to_datetime(time_doy):
    time_hours = [int((itime-int(itime))*24) for itime in (time_doy)]
    time_minutes = [int(((time_doy[itime]-int(time_doy[itime]))*24-time_hours[itime])*60) for itime in range(len(time_doy))]
    time_seconds = [int((((time_doy[itime]-int(time_doy[itime]))*24-time_hours[itime])*60-time_minutes[itime])*60) for itime in range(len(time_doy))]
    time = [datetime.datetime.strptime(f'{int(time_doy[itime])}T{time_hours[itime]:02d}:{time_minutes[itime]:02d}:{time_seconds[itime]:02d}', "%Y%jT%H:%M:%S") for itime in range(len(time_doy))]

    return time


# A function that either writes or updates the json file
def write_json(storage, dataUnits, dataObserver, update=False):
    if update:
        for thing in range(len(storage)):
            with open('polygonData.json', 'r') as js_file:
                times, freqs = mdates.num2date(np.array(storage[thing].vertices)[:, 0]), np.array(storage[thing].vertices)[:, 1]
                name = storage[thing].name
                coords = [[[float(t.mktime(times[i].timetuple())), freqs[i]] for i in range(len(times))]]
                # polygon coordinates need to be in counter-clockwise order (TFCat specification)
                if (LinearRing(coords[0])).is_ccw == False:
                    coords = [coords[0][::-1]]
                the_update = json.load(js_file)
                count = int(the_update['features'][-1]['id'])+1
                js_file.close()
                the_update['features'].append({"type": "Feature", "id": count, "geometry": {"type": "Polygon", "coordinates": coords}, "properties": {"feature_type": name}})

                with open('polygonData.json', 'w') as the_file:
                    json.dump(the_update, the_file)
                    the_file.close()
    else:
        with open('polygonData.json', 'w') as js_file:
            TFCat = {"type": "FeatureCollection", "features": [], "crs": {"name": "Time-Frequency", "properties": {"time_coords": {"id": "unix", "name": "Timestamp (Unix Time)", "unit": "s", "time_origin": "1970-01-01T00:00:00.000Z", "time_scale": "TT"}, "spectral_coords": {"name": "Frequency", "unit": dataUnits}, "ref_position": {"id": dataObserver}}}}
            count = 0
            for thing in range(len(storage)):
                times, freqs = mdates.num2date(np.array(storage[thing].vertices)[:, 0]), np.array(storage[thing].vertices)[:, 1]
                name = storage[thing].name
                coords = [[[float(t.mktime(times[i].timetuple())), freqs[i]] for i in range(len(times))]]
                # polygon coordinates need to be in counter-clockwise order (TFCat specification)
                if (LinearRing(coords[0])).is_ccw == False:
                    coords = [coords[0][::-1]]
                TFCat['features'].append({"type": "Feature", "id": count, "geometry": {"type": "Polygon", "coordinates": coords}, "properties": {"feature_type": name}})
                count += 1

            json.dump(TFCat, js_file)


# A function that either writes or updates the txt file
def write_txt(storage, update=False):
    if update:
        with open('selected_polygons.txt', 'a') as file:
            for ply in range(len(storage)):
                times, freqs = mdates.num2date(np.array(storage[ply].vertices)[:, 0]), np.array(storage[ply].vertices)[:, 1]
                name = storage[ply].name
                file.write(f'{name}, {min(times)}, {max(times)}, {min(freqs)}, {max(freqs)} \n')
    else:
        # if they aren't create a new file
        with open('selected_polygons.txt', 'w') as file:
            file.write('Name, t_0, t_1, f_0, f_1 \n')
            for ply in range(len(storage)):
                times, freqs = mdates.num2date(np.array(storage[ply].vertices)[:, 0]), np.array(storage[ply].vertices)[:, 1]
                name = storage[ply].name
                file.write(f'{name}, {min(times)}, {max(times)}, {min(freqs)}, {max(freqs)} \n')


# writing and categorising polygon vertices to a .txt and .json file
def write_file(storage, dataUnits, dataObserver):
    if not path.exists('selected_polygons.txt'):  # check if the files exist
        write_txt(storage)
        write_json(storage, dataUnits, dataObserver)

    else:  # if files are in directory, open them and add to them
        write_txt(storage, update=True)
        write_json(storage, dataUnits, dataObserver, update=True)


# Opening Json file and extracting previously drawn polygons
def open_and_draw(time_view_start, time_view_end):
    data_array = []
    date_time = [time_view_start, time_view_end]
    unix_start, unix_end = t.mktime(date_time[0].timetuple()), t.mktime(date_time[1].timetuple())
    if path.exists('polygonData.json'):
        with open('polygonData.json', 'r') as dat_file:
            data = json.load(dat_file)
            for i in data['features']:
                time = np.array(i['geometry']['coordinates'])[0][:, 0]
                freq = np.array(i['geometry']['coordinates'])[0][:, 1]
                if any(time >= unix_start) or any(time <= unix_end):
                    coords = []
                    for j in range(len(time)):
                        unix_to_datetime = datetime.datetime.fromtimestamp(time[j])
                        coords.append([mdates.date2num(unix_to_datetime), freq[j]])
                    data_array.append(np.array(coords))
    return data_array


# handling the data
def extract_data(file_data, time_view_start, time_view_end):
    # read the save file and copy variables
    filename = file_data['name']
    time_index = file_data['time']
    freq_index = file_data['freq']
    flux_index = file_data['flux']
    file = readsav(filename)

    time = file[time_index].copy()
    time = np.array(time, dtype=np.datetime64)
    time_view = time[(time >= time_view_start) & (time <= time_view_end)]

    # copy the flux and frequency variable into temporary variable in
    # order to interpolate them in log scale
    s = file[flux_index][:, (time >= time_view_start) & (time <= time_view_end)].copy()
    frequency_tmp = file[freq_index].copy()

    # frequency_tmp is in log scale from f[0]=3.9548001 to f[24] = 349.6542
    # and then in linear scale above so it's needed to transfrom the frequency
    # table in a full log table and einterpolate the flux table (s --> flux
    frequency = 10**(np.arange(np.log10(frequency_tmp[0]), np.log10(frequency_tmp[-1]), (np.log10(max(frequency_tmp))-np.log10(min(frequency_tmp)))/399, dtype=float))
    flux = np.zeros((frequency.size, len(time_view)), dtype=float)

    for i in range(len(time_view)):
        flux[:, i] = np.interp(frequency, frequency_tmp, s[:, i])

    return time_view, frequency, flux


# The setting up and interacting with the plots using polygonSelector
def plot_and_interact(time_view_start, time_view_end, file, colour_in=None, fwd=None, again=False):

    time, freq, flux = extract_data(
        file, time_view_start=time_view_start, time_view_end=time_view_end
    )

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
    ax2.set_title(f'{file["obs"]} Data - {time_view_start} to {time_view_end}', fontsize=fontsize + 2)
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
        ply1 = Poly(ax2, fig2, time_view_start, time_view_end, file)  # Start drawing a polygon
        ply1.name = input('\n Feature label: ')

        print('\n Select the vertices of your polygon with your mouse, complete the shape by clicking on the starting point. \n Edit the shape by drag and dropping any of the vertices on your polygon.')
        print('\n To start a new polygon press enter before providing it with a name. When done, simply press "q" ')
    else:
        ply1 = Poly(ax2, fig2, time_view_start, time_view_end, file)  # Start drawing a polygon
        ply1.name = input('\n Feature label: ')

    fig2.canvas.mpl_connect('key_press_event', ply1.new_poly)
    plt.show(block=True)


if __name__ == '__main__':
    while True:
        try:
            file_name, start_year = input('\n Input RPWS (.sav) data file name and year of origin (e.g. filename.sav, 2006):  ').split(', ')

            if path.exists(file_name):
                if file_name.endswith('.sav'):
                    time_var, freq_var, flux_var = input('Please enter the time, frequency and flux variable names in your file (e.g. t, fq, fx): ').split(', ')
                    break
                else:
                    print(f'\n {file_name} is not a valid data file. Try again...')

            else:
                print('\n File does not exist, please try again...')

        except ValueError:
            print('\n You did not enter the file name and year of origin correctly. Please try again')

    observer, units = input('\n Please enter the observer and units of measurement (e.g. Juno, kHz): ').split(', ')
    file_data = {'name': file_name, 'origin': int(start_year), 'obs': observer, 'units': units, 'time': time_var, 'freq': freq_var, 'flux': flux_var}
    start_day = int(input('\n Please enter your start day (yyyydoy): '))
    end_day = int(input('\n Please enter your end day (yyyydoy): '))
    saved_polys = open_and_draw(start_day, end_day)
    plot_and_interact(start_day, end_day, file_data, colour_in=saved_polys, again=True)
