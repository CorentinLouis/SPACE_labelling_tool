import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
import pandas as pd
import numpy
from astropy.time import Time, TimeDelta
from astropy import units
from astropy.units import Unit
from astropy import constants
from cdflib import CDF
from numpy import ndarray  # Explicit import to make Typing easier
from tqdm import tqdm

from spacelabel.models.dataset import DataSet

log = logging.getLogger(__name__)


class DataSetCDF(DataSet):
    """
    Contains the data from a set of CDF-format observation datafiles.
    """
    @staticmethod
    def exists_preprocessed(file_path: Path) -> Path:
        """
        Does a pre-processed file already exist for this path?

        :param file_path: The path to the file. The filename must be in the format 'stuff_[...]_stuff_YYYYMMDD_vXX.cdf'
        :return: The path to the preprocessed file
        """
        preprocessed_path: Path = file_path.with_name('_'.join(file_path.stem.split('_')[:-2])+'.preprocessed.hdf5')
        return preprocessed_path if preprocessed_path.exists() else None

    @staticmethod
    def _find_config(columns: List[str], config_name: Optional[str]) -> dict:
        """
        Looks for configurations that describe the columns in a file.

        :param columns: The list of columns in the file
        :param config_name: If a config name was passed, what is it?
        """
        configs: Dict[str, dict] = {}
        configs_file_name: List[str] = {}
        # Scan the configs directory for entries
        for config_file in (Path(__file__).parent.parent.parent.parent / 'config' / 'cdf').glob('*.json'):
            configs[config_file.stem] = json.load(config_file.open())
            configs_file_name[config_file.stem] = config_file
    


        if config_name:
            # If there was a config requested, get it!
            if config_name[0] not in configs_file_name.keys():
            #if config_name not in configs.keys():
                raise KeyError(
                    f"Requested a non-existent configuration '{config_name[0]}'. "
                    f"Configurations are: {', '.join(configs.keys())}"
                )

            # Let's check the required columns from the config - do they all exist in the file?
            config = configs[config_name[0]]
            #config_columns = [config['time'], config['frequency']]
            config_columns = [t for t in config['time']] + [f for f in config['frequency']]
            for receiver in config['measurements']:
                for measurement in receiver.values():
                        config_columns.append(measurement['value'])
                        if measurement.get('background', None):
                            config_columns.append(measurement['background'])
            print(config_columns)
            if not set(config_columns).intersection(set(columns)):
                raise KeyError(
                    f"Requested configuration '{config_name[0]}' does not describe the input file. "
                    f"Configuration file requires columns {', '.join(config_columns)}, "
                    f"but the file only contains the columns {', '.join(columns)}."
                )
            else:
                return config

        else:
            # We iterate over each of the possible configurations.
            # Once we find one (and only one) that fully describes the input file, we accept it as the configuration.
            valid_configs: List[dict] = []

            for config_entry in configs.values():
                # Let's check the required columns from the config - do they all exist in the file?
                config_columns = [t for t in config_entry['time']] + [f for f in config_entry['frequency']]
                for receiver in config_entry['measurements']:
                    for measurement in receiver.values():
                        config_columns.append(measurement['value'])
                        if measurement.get('background', None):
                            config_columns.append(measurement['background'])
                if not set(config_columns) - set(columns):
                #if set(config_columns).intersection(set(columns)):
                    valid_configs.append(config_entry)

            print("####### valid config is: ##########")
            print(valid_configs)
            if not valid_configs:
                raise KeyError(
                    f"No configuration files describe the columns of input file. "
                    f"Columns are: {', '.join(columns)}."
                )
            elif len(valid_configs) > 1:
                raise KeyError(
                    f"Too many configuration files describe the columns of input file. "
                    f"Matching configuration files are: "
                    f"{', '.join([config_name for config_name in valid_configs.keys()])}."
                )
            else:
                return valid_configs[0]

    def __init__(
            self,
            file_path: Path,
            config_name: Optional[str] = None,
            log_level: Optional[int] = None
    ):
        """
        Sets up datafiles for reading.

        :param file_path: The path to the file. The filename must be in the format 'stuff_[...]_stuff_YYYYMMDD_vXX.cdf'
        :param config_name: The configuration file to use, if any
        :param log_level: The level of logging to show from this object
        """
        super().__init__(
            # This sets the base file path to be `/a/b/c/stuff_[...]_stuff`
            file_path.with_name('_'.join(file_path.stem.split('_')[:-2])),
            log_level=log_level
        )

        if log_level:
            log.setLevel(log_level)

        # We want to get a list of all the files, then sort it because you can't trust the OS to
        cdf_paths = list(self._file_path.parent.glob(self._file_path.name+'*.cdf'))
        cdf_paths.sort()

        # Find the config for the file based on the column names
        self._config = self._find_config(
            columns=CDF(str(cdf_paths[0])).cdf_info()['zVariables'],
            config_name=config_name
        )

        epochs: List[ndarray] = []
        for cdf_path in tqdm(cdf_paths):
            file: CDF = CDF(str(cdf_path))
            if self._config['time'].count(self._config['time'][0]) == len(self._config['time']):
                epochs.append(file[self._config['time'][0]])
                cdf_time_format = CDF(str(cdf_paths[0])).varinq(self._config['time'][0])['Data_Type_Description']
            else:
                first = True
                for t in self._config['time']:
                    if first == True: 
                        ep = file[t]
                        print(ep)
                        print("In progress")
                        exit(1)
        
        if cdf_time_format == 'CDF_TIME_TT2000':
            cdf_time_format = 'CDF_TT2000'
        
        self._time = Time(
            numpy.concatenate(epochs), 
            format = cdf_time_format.lower())

        
        self._time.format = 'jd'
        self._units['Time'] = "JD"

        first = True
        for f in self._config['frequency']:
            if first == True: 
                fr = file[f] 
                first = False
            else:
                fr = numpy.concatenate((fr, file[f]))
        self._freq = fr
        #We'll probably want to make this more sophiosticated but it will do for a demo
        self._units['Frequency'] = file.varattsget(self._config['frequency'][0])['UNITS'] 

        self._observer = file.globalattsget()['Mission_group']

    def pad(self,
            cdf_file,
            series,
            time_minimum: Optional[float] = None,
            missing_data: Optional[str] = False
            ): 

        if not time_minimum:
            time_minimum = self._config['preprocess'].get('time_minimum', None)
        if time_minimum:
            if time_minimum < 0:
                raise ValueError(f"Requested a negative minimum time bin: {time_minimum}")
            elif TimeDelta(time_minimum, format='sec') < (self._time[1] - self._time[0]):
                log.warning("preprocess: The target time bin is smaller than the time bins in the data; skipping.")
                time_minimum = None
        time_minimum = numpy.timedelta64(time_minimum, 's')
        
        cdf_time_format = cdf_file.varinq(self._config['time'][0])['Data_Type_Description'].lower()
        if cdf_time_format == 'CDF_TIME_TT2000'.lower():
            cdf_time_format = 'CDF_TT2000'.lower()


        if missing_data:
            newtime = Time(pd.date_range(Time(cdf_file[self._config['time'][0]], format = cdf_time_format).datetime64[0], 
                           Time(cdf_file[self._config['time'][0]], format = cdf_time_format).datetime64[-1], 
                           int(numpy.ceil(((
                               Time(cdf_file[self._config['time'][0]], 
                                              format = cdf_time_format).datetime64[-1] - 
                               Time(cdf_file[self._config['time'][0]], 
                                    format = cdf_time_format).datetime64[0])/time_minimum))))).jd
            newdata = numpy.repeat(numpy.nan, len(newtime))
            
            return newtime, newdata       
        else:
            data = cdf_file[series["value"]]
            timefc = Time(cdf_file[series["time"]], format = cdf_time_format).datetime64

            new_time = numpy.array([], dtype = 'datetime64[ns]')
            new_data = numpy.array([], dtype = 'float64')

            if timefc[0] > Time(cdf_file[self._config['time'][0]], format = cdf_time_format).datetime64[0]:
                timefc = numpy.concatenate((numpy.array([Time(cdf_file[self._config['time'][0]], format = cdf_time_format).datetime64[0]]),
                                timefc))
                data = numpy.concatenate((numpy.array([numpy.nan]), data))
            if timefc[-1] < Time(cdf_file[self._config['time'][0]], format = cdf_time_format).datetime64[-1]:
                timefc = numpy.concatenate((timefc,
                                     numpy.array([Time(cdf_file[self._config['time'][0]], format = cdf_time_format).datetime64[-1]])))
                data = numpy.concatenate((data,numpy.array([numpy.nan])))



            for t in range(0, len(timefc)-1):
                if timefc[t+1]-timefc[t] > time_minimum: 
                    new_time = numpy.concatenate((new_time,  
                                              numpy.array(pd.date_range(timefc[t],
                                                                     timefc[t-1],
                                                                     int(numpy.ceil(((timefc[t+1]-timefc[t])/time_minimum))))[:-1])
                                         ))
                    new_data = numpy.concatenate((new_data,  
                                              numpy.array([data[t]]+[numpy.nan for l in range(0, 
                                                                                        int(numpy.ceil((
                                                                                            (timefc[t+1]-timefc[t])/time_minimum)-2
                                                                                        )))])
                                             ))
                else: 
                    new_time = numpy.concatenate((new_time, numpy.array([timefc[t]])))
                    new_data = numpy.concatenate((new_data, numpy.array([data[t]])))

            new_time  = Time(new_time).jd
            return new_time, new_data

    def load(self):
        """
        Reads a datafile in CDF format.
        """

        log.info(f"DataSetCDF: Loading '{self._file_path}[*].cdf...")

        # We want to get a list of all the files, then sort it because you can't trust the OS to
        cdf_paths: List[Path] = list(self._file_path.parent.glob(self._file_path.name+'*.cdf'))
        cdf_paths.sort()

        file: CDF = None
        
        for measurement_name in self._config['measurements'][0].keys(): #Maybe dubious if we want different antenna configs put together
            first = True
            for measure in self._config['measurements']:
                if first == True:
                    measurement_config = measure[measurement_name]
                    measurements: List[ndarray] = []

                    for cdf_path in tqdm(cdf_paths):
                        file = CDF(str(cdf_path))
                        measurements.append(file[measurement_config['value']])
                    first = False
                    # The data is not background-subtracted. Background varies per frequency bin.
                    measurement = numpy.concatenate(measurements)
                    if measurement_config.get('background', None):
                        measurement -= file[measurement_config['background']]

                    # The data may not be in the units we want, so apply the conversion factor
                    if measurement_config.get('conversion', None):
                        measurement *= measurement_config['conversion']

                else:
                    measurement_config = measure[measurement_name]
                    measurements2: List[ndarray] = []
                    for cdf_path in cdf_paths:
                        file = CDF(str(cdf_path))
                            
                        measurements2.append(file[measurement_config['value']])
                    first = False
                    # The data is not background-subtracted. Background varies per frequency bin.
                    measurement2 = numpy.concatenate(measurements2)
                    if measurement_config.get('background', None):
                        measurement2 -= file[measurement_config['background']]

                    # The data may not be in the units we want, so apply the conversion factor
                    if measurement_config.get('conversion', None):
                        measurement2 *= measurement_config['conversion']
                    measurement = numpy.concatenate((measurement,measurement2), axis = 1)
            self._data[measurement_name] = measurement
            self._units[measurement_name] = measurement_config.get('units', None)

        first = True
        for series in self._config['other']:    
            if first == True:  
                measurements: List[ndarray] = []
                times_1d: List[ndarray] = []
                
                total_time_series_measurements = []

                for path in tqdm(cdf_paths):
                    cdf_file = CDF(path)

                    try:
                        total_time_series_measurements.append(len(cdf_file[series["value"]]))
                    except:
                        pass
    
                threshold = numpy.array(total_time_series_measurements).max()-(numpy.array(total_time_series_measurements).max()/(24*30))


                for path in tqdm(cdf_paths):
                    cdf_file = CDF(path)
                    try:
                        if len(cdf_file[series["time"]]) > threshold:
                            cdf_time_format = cdf_file.varinq(series['time'])['Data_Type_Description'].lower()
                            if cdf_time_format == 'CDF_TIME_TT2000'.lower():
                                cdf_time_format = 'CDF_TT2000'.lower()

                            measurements.append(cdf_file[series["value"]])
                            times_1d.append(Time(cdf_file[series["time"]], format = cdf_time_format).jd)
                        else: 
                            t, d = self.pad(cdf_file, series, missing_data = False)
                            measurements.append(d)
                            times_1d.append(t)

                    except:
                        t, d = self.pad(cdf_file, series, missing_data = True)
                        measurements.append(d)
                        times_1d.append(t)
                
    
                
                        
                        
                first = False
                # The data is not background-subtracted. Background varies per frequency bin.
                measurement = numpy.concatenate(measurements)
                time_1d = numpy.concatenate(times_1d)
                if measurement_config.get('background', None):
                    measurement -= file[measurement_config['background']]

                # The data may not be in the units we want, so apply the conversion factor
                if measurement_config.get('conversion', None):
                    measurement *= measurement_config['conversion']


        

            self._time_1d = time_1d        
            self._units_1d['Time'] = "JD"
            
            
            self._data_1d[series["value"]] = measurement
            self._units_1d[series["value"]] = measurement_config.get('units', None)

        log.info(f"DataSetCDF: Loaded '{self._file_path}[*].cdf...'")

# Remember to register datatypes in the datatype reader!
