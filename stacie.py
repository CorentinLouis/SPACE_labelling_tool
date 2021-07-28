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

if any('SPYDER' in name for name in environ):
    matplotlib.use('Qt5Agg')
else:
    pass

plt.ion()


class poly:  # class to make each polygon shape

    def __init__(self, ax, fig):  # initialising
        self.canvas = ax.figure.canvas
        self.ax = ax
        self.fig = fig
        props = dict(color='k', linestyle='--', linewidth=1.5, alpha=0.5)
        self.polygon = PolygonSelector(ax, self.onSelect, useblit=False, lineprops=props)
        self.vertices = []
        self.shapes = []
        self.name = None
        self.end = None
        self.start = None

    # function that deals with the vertices of each polygon when selected
    def onSelect(self, verts):
        self.vertices = verts
        self.end = float(mdates.num2date(max(np.array(self.vertices)[:, 0])).strftime('%Y%j.%H'))

    def newName(self):
        n = input('\n Feature Label: ')
        self.name = n

    def newPoly(self, event):
        if event.key == 'enter':
            a = poly(self.ax, self.onSelect)
            a.newName()
            self.shapes.append(a)
            plt.show()

        if event.key == 'q':
            plt.close(self.fig)

        if event.key == 'escape':
            self.shapes.clear()
            self.vertices.clear()

        if event.key == 'r':
            rename = input('\n Enter new feature label: ')
            self.name = rename

        else:
            return None


# All of this is dealing with the data and plotting the spectrum
def doy2004_to_yyyyddd(doy2004):  # Function to change doy format to yyyyddd

    aa = np.arange(61, dtype=float)+2004  # array of years starting from 2004
    deb = np.zeros([61], dtype=float)  # zeros
    for i in range(1, len(deb)):  # categorising start point for each year
        if i % 4 == 1:
            deb[i:] = deb[i:]+366.
        else:
            deb[i:] = deb[i:]+365.

    yyyyddd = np.zeros(len(doy2004), dtype=float)

    for i in range(0, len(doy2004)):
        j = doy2004[i]-deb
        yyyyddd[i] = (aa[j >= 1][-1])*1000.+j[j >= 1][-1]

    return(yyyyddd)


# convert from doy format to datetime objects
def doy_to_datetime(time_doy):
    time_hours = [int((itime-int(itime))*24) for itime in (time_doy)]
    time_minutes = [int(((time_doy[itime]-int(time_doy[itime]))*24-time_hours[itime])*60) for itime in range(len(time_doy))]
    time_seconds = [int((((time_doy[itime]-int(time_doy[itime]))*24-time_hours[itime])*60-time_minutes[itime])*60) for itime in range(len(time_doy))]
    time = [datetime.datetime.strptime(f'{int(time_doy[itime])}T{time_hours[itime]:02d}:{time_minutes[itime]:02d}:{time_seconds[itime]:02d}', "%Y%jT%H:%M:%S") for itime in range(len(time_doy))]

    return(time)


# A function that either writes or updates the json file
def writeJson(storage, dataUnits, dataObserver, update=False):
    if update:
        for thing in range(len(storage)):
            with open('polygonData.json', 'r') as js_file:
                times, freqs = mdates.num2date(np.array(storage[thing].vertices)[:, 0]), np.array(storage[thing].vertices)[:, 1]
                name = storage[thing].name
                coords = [[float(t.mktime(times[i].timetuple())), freqs[i]] for i in range(len(times))]
                theUpdate = json.load(js_file)
                count = int(theUpdate['features'][-1]['id'])+1
                js_file.close()
                theUpdate['features'].append({"type": "Feature", "id": count, "geometry": {"type": "Polygon", "coordinates": coords}, "properties": {"feature_type": name}})

                with open('polygonData.json', 'w') as theFile:
                    json.dump(theUpdate, theFile)
                    theFile.close()
    else:
        with open('polygonData.json', 'w') as js_file:
            TFCat = {"type": "FeatureCollection", "features": [], "crs": {"name": "Time-Frequency", "properties": {"time_coords": {"id": "unix", "name": "Timestamp (Unix Time)", "unit": "s", "time_origin": "1970-01-01T00:00:00.000Z", "time_scale": "TT"}, "spectral_coords": {"name": "Frequency", "unit": dataUnits}, "ref_position": {"id": dataObserver}}}}
            count = 0
            for thing in range(len(storage)):
                times, freqs = mdates.num2date(np.array(storage[thing].vertices)[:, 0]), np.array(storage[thing].vertices)[:, 1]
                name = storage[thing].name
                coords = [[float(t.mktime(times[i].timetuple())), freqs[i]] for i in range(len(times))]
                TFCat['features'].append({"type": "Feature", "id": count, "geometry": {"type": "Polygon", "coordinates": coords}, "properties": {"feature_type": name}})
                count += 1

            json.dump(TFCat, js_file)


# A function that either writes or updates the txt file
def writeTxt(storage, update=False):
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
def writeFile(storage, dataUnits, dataObserver):
    if not path.exists('selected_polygons.txt'):  # check if the files exist
        writeTxt(storage)
        writeJson(storage, dataUnits, dataObserver)

    else:  # if files are in directory, open them and add to them
        writeTxt(storage, update=True)
        writeJson(storage, dataUnits, dataObserver, update=True)


# Opening Json file and extracting previously drawn polygons
def openAndDraw(startDay, endDay):
    dateTime = doy_to_datetime([startDay, endDay])
    dataArray = []
    unix_start, unix_end = t.mktime(dateTime[0].timetuple()), t.mktime(dateTime[1].timetuple())
    if path.exists('polygonData.json'):
        with open('polygonData.json', 'r') as datFile:
            data = json.load(datFile)
            for i in data['features']:
                time = np.array(i['geometry']['coordinates'])[:, 0]
                freq = np.array(i['geometry']['coordinates'])[:, 1]
                if any(time >= unix_start) and any(time <= unix_end):
                    coords = []
                    for j in range(len(time)):
                        unixToDatetime = datetime.datetime.utcfromtimestamp(time[j])
                        coords.append([mdates.date2num(unixToDatetime), freq[j]])
                    dataArray.append(np.array(coords))
    return dataArray


# handling the data
def plot_spdyn_cassini_rpws(filename, yyyydddb=2004181, yyyyddde=2004181):
    # read the save file and copy variables
    file = readsav(filename)
    time_t04 = file.t.copy()

    # transform the time table (in 'Day since year 2004') into Day of
    # Year and then datetime table
    time_doy_tmp = doy2004_to_yyyyddd(time_t04)
    time_doy = time_doy_tmp[(time_doy_tmp >= yyyydddb) & (time_doy_tmp < yyyyddde+1)]
    time = doy_to_datetime(time_doy)

    # copy the flux and frequency variable into temporary variable in
    # order to interpolate them in log scale
    s = file.s[:, (time_doy_tmp >= yyyydddb) & (time_doy_tmp < yyyyddde+1)].copy()
    frequency_tmp = file.f.copy()

    # frequency_tmp is in log scale from f[0]=3.9548001 to f[24] = 349.6542
    # and then in linear scale above so it's needed to transfrom the frequency
    # table in a full log table and einterpolate the flux table (s --> flux
    frequency = 10**(np.arange(np.log10(frequency_tmp[0]), np.log10(frequency_tmp[-1]), (np.log10(max(frequency_tmp))-np.log10(min(frequency_tmp)))/399, dtype=float))
    flux = np.zeros((frequency.size, len(time)), dtype=float)
    for i in range(len(time)):
        flux[:, i] = np.interp(frequency, frequency_tmp, s[:, i])

    return time, time_doy, frequency, flux


# The setting up and interacting with the plots using polygonSelector
def plotAndInteract(startDay, endDay, filename, dataUnits, dataObserver, colourIn=None, fwd=None):

    time, time_doy, freq, flux = plot_spdyn_cassini_rpws(filename, yyyydddb=startDay, yyyyddde=endDay)

    figsize = (15, 5)

    fontsize = 12

    vmin = flux[flux > 0.].min()
    vmax = flux.max()
    scaleZ = colors.LogNorm(vmin=vmin, vmax=vmax)

    # First plot the data as pcolormesh object and save it as a .png
    fig1, ax1 = plt.subplots(figsize=figsize, constrained_layout=True)
    im1 = ax1.pcolormesh(time_doy, freq, flux, cmap='Spectral_r', norm=scaleZ, shading='auto')

    ax1.set_axis_off()
    plt.savefig('radioSpectra.png', bbox_inches='tight', pad_inches=0)
    plt.close(fig1)
    # Open the image and load into graph to save memory
    image = plt.imread('radioSpectra.png')
    remove('radioSpectra.png')
    fig2, ax2 = plt.subplots(figsize=figsize, sharex=True, sharey=True)
    ax2.set_yscale('log')
    mt = mdates.date2num((min(time), max(time)))

    # Formatting Axes
    ax2.set_xlabel('Time', fontsize=fontsize)
    ax2.set_ylabel('Frequency (kHz)', fontsize=fontsize)
    ax2.set_title(f'Cassini/RPWS data - DoY {startDay} to {endDay}', fontsize=fontsize+2)
    dateFmt = mdates.DateFormatter('%Y-%j\n%H:%M')
    ax2.xaxis.set_major_formatter(dateFmt)

    # Formatting colourbar
    figure = ax2.figure
    divider = axes_grid1.make_axes_locatable(ax2)
    cax = divider.append_axes("right", size=0.15, pad=0.2)
    cb = figure.colorbar(im1, extend='both', shrink=0.9, cax=cax, ax=ax2)
    cb.set_label(r'Intensity (V$^2$/m$^2$/Hz)', fontsize=fontsize+2)

    if colourIn:
        for shape in colourIn:
            ax2.add_patch(Polygon(shape, color='k', linestyle='--', linewidth=1.5, alpha=0.5, fill=False))

    ax2.imshow(image, aspect='auto', extent=[mt[0], mt[1], min(freq), max(freq)])

    # Plotting and interacting
    # Begins by basic instruction

    print('Begin by inputting a name for the feature. ')
    ply1 = poly(ax2, fig2)  # Start drawing a polygon
    ply1.name = input('\n Feature label: ')

    print('\n Select the vertices of your polygon with your mouse, complete the shape by clicking on the starting point. \n Edit the shape by drag and dropping any of the vertices on your polygon.')
    print('\n To start a new polygon press enter before providing it with a name. When done, simply press "q" ')
    fig2.canvas.mpl_connect('key_press_event', ply1.newPoly)
    plt.show(block=True)

    try:
        ply1.end = float(mdates.num2date(max(np.array(ply1.vertices)[:, 0])).strftime('%Y%j.%H'))
        ply1.start = float(mdates.num2date(min(np.array(ply1.vertices)[:, 0])).strftime('%Y%j.%H'))
        ply1.shapes.insert(0, ply1)
        writeFile(ply1.shapes, dataUnits, dataObserver)
        print('\n Polygon data saved to file...')

    except IndexError:
        print('\n No new polygons to save to file...')


fileName = str(input('Input RPWS (.sav) data file name:  '))
while True:
    if path.exists(fileName):
        if fileName.endswith('.sav'):
            break
        else:
            fileName = str(input(f'\n {fileName} is not a valid data file. Try again: '))
    else:
        fileName = str(input('\n File does not exist, please try again: '))

observer, units = input('Please enter the observer and units of measurement (e.g. Juno, kHz): ').split(', ')
startDay = int(input('\n Please enter your start day (yyyydoy): '))
endDay = int(input('\n Please enter your end day (yyyydoy): '))
savedPolys = openAndDraw(startDay, endDay)
plotAndInteract(startDay, endDay, fileName, units, observer, colourIn=savedPolys)
direction = None

# At the end of each loop the user is asked if they want to continue,
# if so then they move to the next time range
ans = input('\n Do you wish to continue cataloging (y/n)? ')
while ans == 'y':
    direction = input('\n Do you wish to scroll to the next or previous time phase (forward/backward)?')
    timeDiff = int(endDay-startDay)

    if direction == 'forward':
        startDay += timeDiff
        endDay += timeDiff

    elif direction == 'backward':
        startDay -= timeDiff
        endDay -= timeDiff

    if int(str(endDay)[-3:]) >= 350:
        startDay = int(input('\n Please enter your start day (yyyydoy): '))
        endDay = int(input('\n Please enter your end day (yyyydoy): '))
        savedPolys = openAndDraw(startDay, endDay)
        plotAndInteract(startDay, endDay, fileName, units, observer, colourIn=savedPolys)
        ans = input('\n Do you wish to continue cataloging (y/n)? ')
    else:
        savedPolys = openAndDraw(startDay, endDay)
        plotAndInteract(startDay, endDay, fileName, units, observer, colourIn=savedPolys)
        ans = input('\n Do you wish to continue cataloging (y/n)? ')
