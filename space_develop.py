import datetime

import numpy as np
from os import path, remove, environ
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits import axes_grid1
import matplotlib.colors as colors
from matplotlib.patches import Polygon
import platform

from space_label.io import open_and_draw, extract_data
from space_label.poly import Poly

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


# The setting up and interacting with the plots using polygonSelector
def plot_and_interact(date_start, date_end, file, colour_in=None, fwd=None, again=False):

    time, freq, flux = extract_data(file, date_start=date_start, date_end=date_end)

    figsize = (15, 5)

    fontsize = 12

    vmin = np.quantile(flux[flux>0.], 0.05)
    vmax = np.quantile(flux[flux>0.], 0.95)
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
    ax2.set_title(f'{file["obs"]} Data - DoY {date_start} to {date_end}', fontsize=fontsize + 2)
    dateFmt = mdates.DateFormatter('%Y-%j\n%H:%M')
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

    fig2.canvas.mpl_connect('key_press_event', ply1.new_poly)
    plt.show(block=True)


if __name__ == '__main__':
    while True:
        try:
            file_name = input('\n Input RPWS (.sav) data file name (e.g. filename.sav):  ')

            if path.exists(file_name):
                if file_name.endswith('.sav'):
                    time_var, freq_var, flux_var = input('Please enter the time, frequency and flux variable names in your file (e.g. t, fq, fx): ').split(', ')
                    break
                else:
                    print(f'\n {file_name} is not a valid data file. Try again...')

            else:
                print('\n File does not exist, please try again...')

        except ValueError:
            print('\n You did not enter the file name. Please try again')

    observer, units = input('\n Please enter the observer and units of measurement (e.g. Juno, kHz): ').split(', ')
    file_data = {'name': file_name, 'obs': observer, 'units': units, 'time': time_var, 'freq': freq_var, 'flux': flux_var}
    date_start = datetime.datetime.fromisoformat(input('\n Please enter your start day (YYYY-DD-MM): '))
    date_end = datetime.datetime.fromisoformat(input('\n Please enter your end day (YYYY-DD-MM): '))
    saved_polys = open_and_draw(date_start, date_end)
    plot_and_interact(date_start, date_end, file_data, colour_in=saved_polys, again=True)
