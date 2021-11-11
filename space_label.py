#! /usr/bin/python3
"""
SPACE Labelling Tool

Utility to allow for identification of radio features from spacecraft observations via a GUI.

usage: space_label.py [-h] [-s SPACECRAFT] [-y YEAR_ORIGIN] FILE DATE DATE

positional arguments:
  FILE            The name of the IDL .sav file to analyse
  DATE            The window of days to plot, in YYYYDDD format, e.g. '2003334
                  2003365' for December 2003. The data will be scrolled through
                  in blocks of this window's width.

optional arguments:
  -h, --help      show this help message and exit
  -s SPACECRAFT   The name of the spacecraft. Auto-detected from the input file
                  columns, but required if multiple spacecraft describe the
                  same input file. Valid options are: cassini, juno.
  -y YEAR_ORIGIN  The year of origin, from which times in the dataset are the
                  data set was taken. Auto-detected from the first number in
                  the input file name, but can be provided if there is none,
                  or if this is incorrect.

The code will attempt to identify which spacecraft the data file format corresponds to, and read the file intelligently.
If it can't fit one of them, it will prompt the user to create a new spacecraft configuration file.
In the case of a file matching multiple spacecraft formats, the user is prompted to select one.

"""
import argparse
import json
import re
from pathlib import Path
from scipy.io import readsav
from typing import Dict, List
from datetime import datetime, timedelta

from space_develop import open_and_draw, plot_and_interact


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Read and process spacecraft radio data files in IDL .sav format."
    )
    parser.add_argument(
        "file", type=str, nargs=1, metavar="FILE",
        help="The name of the IDL .sav file to analyse."
    )
    parser.add_argument(
        'date_range', type=int, nargs=2, metavar="DATE",
        help="The window of days to plot, in YYYYDDD format, e.g. '2003334 2003365' for December 2003."
             "The data will be scrolled through in blocks of this window's width."
    )

    parser.add_argument(
        '-s', type=str, nargs=1, dest='config', metavar="SPACECRAFT",
        help="The name of the spacecraft. Auto-detected from the input file columns, "
             "but required if multiple spacecraft describe the same input file. Valid options are: {}.".format(
                ', '.join([str(config_file.stem) for config_file in (Path(__file__).parent / 'config').iterdir()])
             )
    )
    parser.add_argument(
        '-y', type=int, nargs=1, dest='year_origin',
        help="The year of origin, from which times in the dataset are taken. "
             "Auto-detected from the first number in the input file name, "
             "but can be provided if there is none, or if this is incorrect."
    )
    arguments = parser.parse_args()

    # ==================== INPUT FILE ====================
    # First, we load the input file
    input_file: Path = Path(arguments.file[0])
    if not input_file.suffix == '.sav':
        raise ValueError(f"File '{input_file}' is not a '.sav' file")
    elif not input_file.exists():
        raise FileNotFoundError(f"File '{input_file}' does not exist")

    try:
        sav = readsav(str(input_file), python_dict=True)
    except Exception:
        raise ValueError(f"File '{input_file}' is not a valid '.sav' file")

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
        valid_configs: List[dict] = []
        for config_entry in configs.values():
            # print(config_entry, '\n', set(sav.keys()), '\n', set(config_entry['names'].values()))
            if not set(sav.keys()) - set(config_entry['names'].values()):
                valid_configs.append(config_entry)

        if not valid_configs:
            raise FileNotFoundError(
                f"No configuration files describe the columns of input file '{input_file}'.\n"
                f"Columns are: {', '.join(sav.keys())}."
            )
        elif len(valid_configs) > 1:
            raise ValueError(
                f"Too many configuration files describe the columns of input file '{input_file}'.\n"
                f"Matching configuration files are: {', '.join([config['name'] for config in valid_configs])}."
            )
        else:
            config = valid_configs[0]

    # ==================== DATA YEAR ====================
    # Now we figure out the data year, either from the command line or the filename (e.g. 'SKR_2005.sav')
    if arguments.year_origin:
        year_origin: int = int(arguments.year_origin)
    else:
        year_origin: List[str] = re.findall(r'\d+', input_file.stem)
        if not year_origin:
            raise ValueError(
                f"No year in '{input_file}' name and no year of origin provided with the '-y' argument.\n"
                f"Year of origin can be provided as the first number in the input file name, e.g. 'SKR_2004_11_12.sav'."
            )
        else:
            # If there are multiple numbers present in the filename, select the first
            year_origin: int = int(year_origin[0])

    # We validate the data year - is it in the range the satellite operated within?
    data_start = datetime(year=year_origin, month=1, day=1) + timedelta(days=sav[config['names']['time']][0])
    data_end = datetime(year=year_origin, month=1, day=1) + timedelta(days=sav[config['names']['time']][-1])

    if data_start.year < config['years'][0] or data_end.year > config['years'][-1]:
        raise ValueError(
            f"Year range {data_start.year}-{data_end.year} in '{input_file}' is outside of the spacecraft "
            f"{config['name']} operating window of {config['years'][0]}-{config['years'][1]}.\n" +
            (
                f"The year {year_origin} detected from the the file name may be incorrect - "
                f"please provide the year-of-origin with the '-y' argument." if not arguments.year_origin else
                f"The year {year_origin} provided with the '-y' argument may be incorrect."
            )
        )

    # ==================== DATE RANGE ====================
    # Now we have the year of origin, we can validate the date range provided
    date_start = datetime.strptime(str(arguments.date_range[0]), "%Y%j")
    date_end = datetime.strptime(str(arguments.date_range[1]), "%Y%j")

    if date_start < data_start or date_end > data_end:
        raise ValueError(
            f"Date range {date_start}-{date_end} is outside of the data file range {data_start}-{data_end}.\n"
            f"Please check the format of your date range is in YYYYDDD Julian day format, and your year-of-origin " +
            (
                f"{year_origin} detected from the file name is correct. You must provide the year-of-origin via "
                f"the '-y' argument if not." if not arguments.year_origin else
                f"{year_origin} provided with the '-y' argument is correct."
            )
        )

    # ==================== CALL SPACE_DEVELOP ====================
    # We've now validated all the input files and arguments. Let's pass all that data to space_develop.py.
    # This is just a copy-paste of the calls at the end of space_develop.py.

    saved_polys = open_and_draw(
        arguments.date_range[0], arguments.date_range[1]
    )
    plot_and_interact(
        arguments.date_range[0], arguments.date_range[1],
        {
            'name': input_file, 'origin': year_origin, 'obs': config['observer'],
            'units': config['units']['frequency'],
            'time': config['names']['time'],
            'freq': config['names']['frequency'],
            'flux': config['names']['flux_density'],
        },
        colour_in=saved_polys, again=True
    )
