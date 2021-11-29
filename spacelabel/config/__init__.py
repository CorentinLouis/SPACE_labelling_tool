import json

from pathlib import Path
from typing import List, Dict


def find_config_for_sav(sav: Dict) -> dict:
    """

    :param sav:
    """
    # First, we scan the configs directory for entries
    configs: Dict[str, dict] = {}
    for config_file in (Path(__file__).parent.parent.parent / 'config').glob('*.json'):
        configs[config_file.stem] = json.load(config_file.open())

    # We iterate over each of the possible configurations.
    # Once we find one (and only one) that fully describes the input file, we accept it as the configuration.
    valid_configs: List[dict] = []
    for config_entry in configs.values():
        # print(config_entry, '\n', set(sav.keys()), '\n', set(config_entry['names'].values()))
        if not set(sav.keys()) - set(config_entry['names'].values()):
            valid_configs.append(config_entry)

    if not valid_configs:
        raise KeyError(
            f"No configuration files describe the columns of input file.'.\n"
            f"Columns are: {', '.join(sav.keys())}."
        )
    elif len(valid_configs) > 1:
        raise KeyError(
            f"Too many configuration files describe the columns of input file.\n"
            f"Matching configuration files are: {', '.join([config['name'] for config in valid_configs])}."
        )
    else:
        return valid_configs[0]
