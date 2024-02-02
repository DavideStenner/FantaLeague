import os
import json

from typing import Dict, Any

def import_config(config_path: str='config/config.json') -> Dict[str, Any]:
    with open(config_path) as config_file:
        config = json.load(config_file)

    return config

def import_credential(config_path: str='config/credential.json') -> Dict[str, Any]:
    with open(config_path) as config_file:
        config = json.load(config_file)

    return config

def import_mapping_artists(mapping_path: str='mapping/mapping_artists.json') -> Dict[str, Any]:
    with open(mapping_path) as file:
        mapping = json.load(file)

    return mapping

def set_key_env() -> None:
    """
    Set credential as os environ

    """
    credential = import_credential()

    for key, value in credential.items():
        os.environ[key] = value