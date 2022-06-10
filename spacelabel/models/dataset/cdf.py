import json
import logging
from pathlib import Path
from typing import Dict, Optional, List

import numpy
from astropy.time import Time
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
        # Scan the configs directory for entries
        for config_file in (Path(__file__).parent.parent.parent.parent / 'config' / 'cdf').glob('*.json'):
            configs[config_file.stem] = json.load(config_file.open())

        if config_name:
            # If there was a config requested, get it!
            if config_name not in configs.keys():
                raise KeyError(
                    f"Requested a non-existent configuration '{config_name}'. "
                    f"Configurations are: {', '.join(configs.keys())}"
                )

            # Let's check the required columns from the config - do they all exist in the file?
            config = configs[config_name]
            config_columns = [config['time'], config['frequency']]
            for measurement in config['measurements'].values():
                config_columns.append(measurement['value'])
                if measurement.get('background', None):
                    config_columns.append(measurement['background'])

            if set(config_columns) - set(columns):
                raise KeyError(
                    f"Requested configuration '{config_name}' does not describe the input file. "
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
                config_columns = [config_entry['time'], config_entry['frequency']]
                for measurement in config_entry['measurements'].values():
                    config_columns.append(measurement['value'])
                    if measurement.get('background', None):
                        config_columns.append(measurement['background'])

                if not set(config_columns) - set(columns):
                    valid_configs.append(config_entry)

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
            epochs.append(file[self._config['time']])

        self._time = Time(
            numpy.concatenate(epochs), format='cdf_tt2000'
        )

        self._time.format = 'jd'
        self._units['Time'] = "JD"

        self._freq = file[self._config['frequency']]
        self._units['Frequency'] = file.varattsget(self._config['frequency'])['UNITS']

        self._observer = file.globalattsget()['Mission_group']

    def load(self):
        """
        Reads a datafile in CDF format.
        """
        super().load()

        log.info(f"DataSetCDF: Loading '{self._file_path}[*].cdf...")

        # We want to get a list of all the files, then sort it because you can't trust the OS to
        cdf_paths: List[Path] = list(self._file_path.parent.glob(self._file_path.name+'*.cdf'))
        cdf_paths.sort()

        file: CDF = None
        for measurement_name in self._config['measurements'].keys():
            measurement_config = self._config['measurements'][measurement_name]
            measurements: List[ndarray] = []
            for cdf_path in cdf_paths:
                file = CDF(str(cdf_path))
                measurements.append(file[measurement_config['value']])

            # The data is not background-subtracted. Background varies per frequency bin.
            measurement = numpy.concatenate(measurements)
            if measurement_config.get('background', None):
                measurement -= file[measurement_config['background']]

            # The data may not be in the units we want, so apply the conversion factor
            if measurement_config.get('conversion', None):
                measurement *= measurement_config['conversion']

            self._data[measurement_name] = measurement
            self._units[measurement_name] = measurement_config.get('units', None)

        log.info(f"DataSetCDF: Loaded '{self._file_path}[*].cdf...'")

# Remember to register datatypes in the datatype reader!
