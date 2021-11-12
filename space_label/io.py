import datetime
import json
import time as t
from os import path

import numpy as np
from matplotlib import dates as mdates
from scipy.io import readsav
from shapely.geometry import LinearRing


# A function that either writes or updates the txt file
def write_txt(storage, update=False):
    with open('selected_polygons.txt', 'a' if update else 'w') as file:
        if not update:
            file.write('Name, t_0, t_1, f_0, f_1 \n')

        for ply in range(len(storage)):
            times, freqs = mdates.num2date(np.array(storage[ply].vertices)[:, 0]), np.array(storage[ply].vertices)[:, 1]
            name = storage[ply].name
            file.write(f'{name}, {min(times)}, {max(times)}, {min(freqs)}, {max(freqs)} \n')


# writing and categorising polygon vertices to a .txt and .json file
def write_file(storage, dataUnits, dataObserver):
    update = path.exists('selected_polygons.txt')  # check if the files exist, if so, open them and add to them
    write_txt(storage, update=update)
    write_json(storage, dataUnits, dataObserver, update=update)


# Opening Json file and extracting previously drawn polygons
def open_and_draw(start_day, end_day):
    date_time = [start_day, end_day]
    data_array = []
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
                        unix_to_datetime = datetime.datetime.utcfromtimestamp(time[j])
                        coords.append([mdates.date2num(unix_to_datetime), freq[j]])
                    data_array.append(np.array(coords))
    return data_array


# handling the data
def extract_data(file_data, date_start, date_end):
    # read the save file and copy variables
    filename = file_data['name']
    freq_index = file_data['freq']
    flux_index = file_data['flux']
    file = readsav(filename)

    # Extract the time from the data
    time = file[file_data['time']]

    # copy the flux and frequency variable into temporary variable in
    # order to interpolate them in log scale
    s = file[flux_index][:, (time >= date_start) & (time <= date_end)].copy()
    frequency_tmp = file[freq_index].copy()

    # frequency_tmp is in log scale from f[0]=3.9548001 to f[24] = 349.6542
    # and then in linear scale above so it's needed to transform the frequency
    # table in a full log table and interpolate the flux table (s --> flux
    frequency = 10**(np.arange(np.log10(frequency_tmp[0]), np.log10(frequency_tmp[-1]), (np.log10(max(frequency_tmp))-np.log10(min(frequency_tmp)))/399, dtype=float))
    flux = np.zeros((frequency.size, len(time)), dtype=float)
    for i in range(len(time)):
        flux[:, i] = np.interp(frequency, frequency_tmp, s[:, i])

    return time, frequency, flux


# A function that either writes or updates the json file
def write_json(storage, dataUnits, dataObserver, update=False):
    if update:
        for thing in range(len(storage)):
            with open('polygonData.json', 'r') as js_file:
                times, freqs = mdates.num2date(np.array(storage[thing].vertices)[:, 0]), np.array(storage[thing].vertices)[:, 1]
                name = storage[thing].name
                coords = [[[float(t.mktime(times[i].timetuple())), freqs[i]] for i in range(len(times))]]
                # polygon coordinates need to be in counter-clockwise order (TFCat specification)
                if not (LinearRing(coords[0])).is_ccw:
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
                if not (LinearRing(coords[0])).is_ccw:
                    coords = [coords[0][::-1]]
                TFCat['features'].append({"type": "Feature", "id": count, "geometry": {"type": "Polygon", "coordinates": coords}, "properties": {"feature_type": name}})
                count += 1

            json.dump(TFCat, js_file)
