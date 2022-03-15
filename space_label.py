#! /usr/bin/python3
import argparse
import json
import logging
import os
from astropy.time import Time
from h5py import File
from pathlib import Path

from typing import Dict

from spacelabel.models.dataset.hdf5 import DataSetHDF5
from spacelabel.views.matplotlib import ViewMatPlotLib
from spacelabel.presenters import Presenter


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Read and process spacecraft radio data files in IDL .sav format."
    )
    parser.add_argument(
        "file", type=str, nargs=1, metavar="FILE",
        help="The name of the HDF5 file to analyse."
    )
    parser.add_argument(
        'date_range', type=str, nargs=2, metavar="DATE",
        help="The window of days to plot, in ISO YYYY-MM-DD format, e.g. '2004-12-1 2004-12-31' for December 2004."
             "The data will be scrolled through in blocks of this window's width."
    )

    parser.add_argument(
        '-s', type=str, nargs=1, dest='config', metavar="SPACECRAFT",
        help="The name of the spacecraft. Auto-detected from the input file columns, "
             "but required if multiple spacecraft describe the same input file. Valid options are: {}.".format(
                ', '.join([str(config_file.stem) for config_file in (Path(__file__).parent / 'config').iterdir()])
             )
    )
    arguments = parser.parse_args()

    # ==================== INPUT FILE ====================
    # First, we load the input file
    input_file: Path = Path(arguments.file[0])

    if input_file.suffix != '.hdf5':
        raise ValueError(f"File '{input_file}' is not a '.hdf5' file")
    elif not input_file.exists():
        raise FileNotFoundError(f"File '{input_file}' does not exist")

    try:
        file_hdf = File(input_file)
    except Exception as e:
        raise ValueError(f"File '{input_file}' is not a valid '.hdf5' file")

    # ==================== SATELLITE CONFIGURATION ====================
    # First, we scan the configs directory for entries
    configs: Dict[str, dict] = {}
    for config_file in (Path(__file__).parent / 'config').glob('*.json'):
        configs[config_file.stem] = json.load(config_file.open())

    # Now, we decide on which satellite should be used
    if arguments.config:
        # If we've been provided a configuration option, and it's in our list of configs, use it,
        # otherwise report that it's wrong to the user
        if arguments.config in configs.keys():
            config = arguments.config
        else:
            raise FileNotFoundError(
                f"Spacecraft '{arguments.config}' is not one of the available configurations.\n"
                f"Options are: {','.join(configs.keys())}."
            )

    else:
        # We iterate over each of the possible configurations.
        # Once we find one (and only one) that fully describes the input file, we accept it as the configuration.
        valid_configs: dict = {}
        for config_name, config_entry in configs.items():
            if not set(file_hdf.keys()) - set(config_entry['names'].values()):
                valid_configs[config_name] = config_entry

        if not valid_configs:
            raise FileNotFoundError(
                f"No configuration files describe the columns of input file '{input_file}'.\n"
                f"Columns are: {', '.join(file_hdf.keys())}."
            )
        elif len(valid_configs) > 1:
            raise ValueError(
                f"Too many configuration files describe the columns of input file '{input_file}'.\n"
                f"Matching options are: {', '.join([valid_config for valid_config in valid_configs.keys()])}."
            )
        else:
            config = list(valid_configs.values())[0]

    # ==================== DATE RANGE ====================
    # Validate the date range provided against the data in the file.
    try:
        date_start = Time(arguments.date_range[0], format='isot')
        date_end = Time(arguments.date_range[1], format='isot')
    except Exception:
        raise ValueError(
            f"Date range {arguments.date_range} is not in ISO date format.\n"
            f"Please provide the dates in the format YYYY-MM-DD e.g. 2005-01-01."
        )

    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

    # Set up the MVP and go!
    dataset: DataSetHDF5 = DataSetHDF5(
        file_path=input_file, config=config, file=file_hdf,
        log_level=logging.INFO
    )

    dataset.validate_dates((date_start, date_end))
    view: ViewMatPlotLib = ViewMatPlotLib(log_level=logging.INFO)
    presenter: Presenter = Presenter(dataset, view, log_level=logging.INFO)
    presenter.request_measurements()
    presenter.request_data_time_range(time_start=date_start, time_end=date_end)
    presenter.run()
