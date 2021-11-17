import datetime

from os import path, environ
import matplotlib
from matplotlib import pyplot as plt
import platform

from spacelabel.poly import plot_and_interact
from spacelabel.io import open_and_draw

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
