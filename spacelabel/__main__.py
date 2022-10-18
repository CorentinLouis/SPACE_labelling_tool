#! /usr/bin/python3
import argparse
import json
import logging
import os
from astropy.time import Time
from h5py import File
from pathlib import Path

from typing import Dict, Type, Tuple

from spacelabel.models.dataset import DataSet
from spacelabel.models.dataset.load import load_dataset, DATASET_TYPES
from spacelabel.views.matplotlib import ViewMatPlotLib
from spacelabel.presenters import Presenter


def main():
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
        '-s', type=str, nargs=1, dest='config', metavar="SPACECRAFT", default=None,
        help="The name of the spacecraft. Auto-detected from the input file columns, "
             "but required if multiple spacecraft describe the same input file."
    )
    parser.add_argument(
        '-f', type=int, nargs=1, dest='frequency_resolution', metavar="FREQUENCY_RESOLUTION", default=None,
        help="The number of frequency bins in log space to rebin the data to. "
             "To override a spacecraft default with 'Do not rebin', set to 0."
    )
    parser.add_argument(
        '-t', type=int, nargs=1, dest='time_minimum', metavar="TIME_MINIMUM", default=None,
        help="The minimum width of time bin, in seconds, to rebin the data to. "
             "To override a spacecraft default with 'Do not rebin', set to 0."
    )
    parser.add_argument(
        '-fig_size', type = float,  nargs = 2, dest = 'fig_size', metavar="FIGURE_SIZE", default=(15, 9),
        help = "Size of the matplotlib figure"
    )
    parser.add_argument(
        '-frac_dyn_range', type=float, nargs=2, dest='frac_dyn_range', metavar="FRAC_DYN_RANGE", default=[0.05, 0.95],
        help="The minimum and maximum fraction of the flux to be display in the dynamic range"
    )
    parser.add_argument(
        '-cmap', type=str, dest='color_map', metavar = 'CMAP', default='viridis',
        help="The name of the color map that will be used for the intensity plot"
    )
    parser.add_argument(
        '-cfeatures', type=str, dest='color_features', metavar='CFEATURES', default='tomato',
        help="The name of the colour for the saved features of interest polygons"
    )
    parser.add_argument(
        '-thickness_features', type=float, dest='thickness_features', metavar='TFEATURES', default=2,
        help="The thickness value for the saved features of interest polygons"
    )
    parser.add_argument(
        '-size_features_name', type=float, dest='size_features_name', metavar='SFEATURESNAME', default=14,
        help="The font size for the name of the saved features of interest polygons"
    )
    parser.add_argument(
        '-g', type=float, nargs='*', dest='frequency_guide', metavar="FREQUENCY_GUIDE", default=None,
        help="Draws horizontal line(s) on the visualisation at these specified frequencies to aid in interpretation of the plot."
             "Values must be in the same units as the data."
              "Lines can be toggled using check boxes."
    )
    parser.add_argument(
        '--not_verbose', dest='not_verbose', action='store_false',
        help="If not_verbose is called, the debug log will not be printed. By default: verbose mode"
    )
        



    arguments = parser.parse_args()

    # ==================== INPUT FILE ====================
    # First, we load the input file
    input_file: Path = Path(arguments.file[0])

    if input_file.suffix not in DATASET_TYPES.keys():
        raise ValueError(
            f"File '{input_file}' is not a valid format! Supported formats are: {', '.join(DATASET_TYPES.keys())}"
        )
    elif not input_file.exists():
        raise FileNotFoundError(f"File '{input_file}' does not exist")

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
    if arguments.not_verbose == True:
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

    # Set up the MVP and go!
    dataset: DataSet = load_dataset(
        file_path=input_file,
        config_name=arguments.config,
        log_level=logging.DEBUG
    )
    dataset.validate_dates((date_start, date_end))
    dataset.load()  # Load the dataset if the dates are valid
    dataset.preprocess(
        frequency_resolution=(arguments.frequency_resolution[0] if arguments.frequency_resolution else None),
        time_minimum=(arguments.time_minimum[0] if arguments.time_minimum else None)
    )
    view: ViewMatPlotLib = ViewMatPlotLib(log_level=logging.INFO)
    presenter: Presenter = Presenter(dataset, view, log_level=logging.INFO)
    presenter.request_measurements()

    presenter.request_data_time_range(
        time_start=date_start, 
        time_end=date_end, 
        fig_size=arguments.fig_size,
        frac_dyn_range=arguments.frac_dyn_range, 
        color_map=arguments.color_map,
        color_features=arguments.color_features,
        thickness_features=arguments.thickness_features,
        size_features_name = arguments.size_features_name,
        frequency_guide=arguments.frequency_guide)

    presenter.run()


if __name__ == '__main__':
   main()
