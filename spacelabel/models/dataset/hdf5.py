import json
import logging
from pathlib import Path
from typing import Dict, Optional, List

import numpy
from astropy.time import Time
from h5py import File

from spacelabel.models.dataset import DataSet

log = logging.getLogger(__name__)


class DataSetHDF5(DataSet):
    """
    Contains the data from an HDF5-format observation datafile.
    """
    @staticmethod
    def exists_preprocessed(file_path: Path) -> Path:
        """
        Does a pre-processed file already exist for this path?

        :param file_path: The path to the file. The filename must be in the format 'stuff_[...]_stuff_YYYYMMDD_vXX.cdf'
        :return: The path to the preprocessed file
        """
        preprocessed_path = file_path.with_suffix('.preprocessed.hdf5')
        return preprocessed_path if preprocessed_path.exists() else None

    @staticmethod
    def _find_config(columns: List[str], config_name: Optional[str]) -> dict:
        """
        Looks for configurations that match the list of columns in a file.

        :param columns: The list of columns in the file
        :param config_name: If a config name was passed, what is it?
        """
        configs: Dict[str, dict] = {}
        # Scan the configs directory for entries
        for config_file in (Path(__file__).parent.parent.parent.parent / 'config' / 'hdf').glob('*.json'):
            configs[config_file.stem] = json.load(config_file.open())

        if config_name:
            # If there was a config requested, vet it!
            if config_name not in configs.keys():
                raise KeyError(
                    f"Requested a non-existent configuration '{config_name}'.\n"
                    f"Configurations are: {', '.join(configs.keys())}"
                )

            # Let's check the required columns from the config - do they all exist in the file?
            config = configs[config_name]
            config_columns = [config['time'], config['frequency']]
            for measurement in config['measurements'].values():
                config_columns.append(measurement['value'])

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
            valid_configs: Dict[str, Dict] = {}

            for config_name, config_entry in configs.items():
                # Let's check the required columns from the config - do they all exist in the file?
                config_columns = [config_entry['time']['value'], config_entry['frequency']['value']]
                for measurement in config_entry['measurements'].values():
                    config_columns.append(measurement['value'])

                if not set(config_columns) - set(columns):
                    valid_configs[config_name] = config_entry

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
                # Take only the 'value' part as it pops as key:value
                return valid_configs.popitem()[1]

    def __init__(
            self,
            file_path: Path,
            config_name: Optional[str] = None,
            log_level: Optional[int] = None
    ):
        """
        Sets up a datafile for reading.

        :param file_path: The path to the file
        :param config_name: The configuration file to use, if any
        :param log_level: The level of logging to show from this object
        """
        super().__init__(file_path, log_level=log_level)

        file: File = File(file_path)
        self._file_path = file_path.with_suffix('')

        # Find a configuration, or validate the one we have been passed
        self._config = self._find_config(list(file.keys()), config_name)

        if log_level:
            log.setLevel(log_level)

        # Save time so we can validate the dates
        self._time = Time(file[self._config['time']['value']], format='jd')
        self._units['Time'] = self._config['time']['units']

        self._freq = numpy.array(file[self._config['frequency']['value']])
        self._units['Frequency'] = self._config['frequency']['units']

        self._observer = self._config['observer']

    def load(self):
        """
        Reads a datafile in HDF5 format using the config file set earlier.
        """
        super().load()

        log.info(f"DataSetHDF5: Loading '{self._file_path.with_suffix('.hdf5')}...")
        file: File = File(self._file_path.with_suffix('.hdf5'))

        for measurement_name, measurement in self._config['measurements'].items():
            # For each of the dependent variables in the config file, are any of them present in the file?
            if measurement['value'] in file.keys():
                # Transpose as the data is stored frequency-major (???)
                self._data[measurement_name] = numpy.array(file[measurement['value']]).T
                self._units[measurement_name] = measurement.get('units', '')

        log.info(f"DataSetHDF5: Loaded '{self._file_path}'")

# Remember to register datatypes in the datatype reader!
