# load and save data to data.json
#

import os
import json
import traceback
from ts_logger import logger
from datetime import datetime
import yaml

settings = dict(cameras={})


def load_settings():
    """
    Load data from settings.yaml
    """
    logger.debug('Loading settings from settings.yaml')
    try:
        with open('settings.yaml', 'r', encoding='utf-8') as f:
            settings.update(yaml.load(f, Loader=yaml.FullLoader))
        return True
    except FileNotFoundError:
        logger.error('settings.yaml not found')
        return False
    except yaml.YAMLError:
        logger.error('settings.yaml is not a valid YAML file')
        return False
    except Exception as e:
        logger.error(f'Unknown error while loading settings.yaml: {e}')
        return False

def save_settings():
    """
    Save data to settings.yaml
    """
    logger.debug('Saving settings to settings.yaml')
    try:
        with open('settings.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(settings, f)
    except:
        logger.error('Failed to save settings to settings.yaml')
        logger.error(traceback.format_exc())
        return False
    return True


def reset_offset_data(marker_uri):
    """
    Reset offset data for marker
    """
    logger.debug(f'Resetting offset data for marker {marker_uri}')
    try:
        camera_id, marker_id = marker_uri.split('.')
        offset_data_dir = os.path.join("offsets", camera_id, marker_id)
        if not os.path.exists(offset_data_dir):
            os.makedirs(offset_data_dir)
        with open(os.path.join(offset_data_dir, 'offset.json'), 'w', encoding='utf-8') as f:
            json.dump(dict(offsets=[]), f, ensure_ascii=False, indent=4)
        return True
    except:
        logger.error(f'Failed to reset offset data for marker {marker_uri}')
        logger.error(traceback.format_exc())
        return False


def save_offset_data(camera_id, marker_id, offset_data):
    """
    Save offset data to disk
    """
    logger.debug(f'Saving offset data for marker {camera_id}.{marker_id}')
    offset_data_dir = os.path.join("offsets", camera_id, "check_log")
    try:
        # append to marker file
        if not os.path.exists(offset_data_dir):
            os.makedirs(offset_data_dir)
        with open(os.path.join(offset_data_dir, f'{marker_id}.dat'), 'a', encoding='utf-8') as f:
            f.write(f"{offset_data['time']}||{offset_data['mmpp']}||{offset_data['x']}||{offset_data['y']}\n")
    except:
        logger.error(f'Failed to save offset data for marker {camera_id}.{marker_id}')
        logger.error(traceback.format_exc())
        return False
    return True
