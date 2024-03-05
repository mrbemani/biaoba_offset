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


def load_offset_data(marker_uri):
    """
    Load offset data from offset.json
    """
    logger.debug(f'Loading offset data for marker {marker_uri}')
    try:
        camera_id, marker_id = marker_uri.split('.')
        offset_data_dir = os.path.join("offsets", camera_id, marker_id)
        if not os.path.exists(offset_data_dir):
            os.makedirs(offset_data_dir)
        if not os.path.exists(os.path.join(offset_data_dir, 'offset.json')):
            with open(os.path.join(offset_data_dir, 'offset.json'), 'w', encoding='utf-8') as f:
                json.dump(dict(offsets=[]), f, ensure_ascii=False, indent=4)
        _offset_file = json.load(open(os.path.join(offset_data_dir, 'offset.json'), 'r', encoding='utf-8'))
        for offset in _offset_file['offsets']:
            offset['time'] = datetime.fromtimestamp(offset['time'])
        return _offset_file['offsets']
    except:
        logger.error(f'Failed to load offset data for marker {marker_uri}')
        logger.error(traceback.format_exc())
        return []

def save_offset_data(marker_uri, offset_data):
    """
    Save offset data to offset.json
    """
    logger.debug(f'Saving offset data for marker {marker_uri}')
    _save_data = []
    for offset in offset_data:
        if isinstance(offset['time'], datetime) and offset['time'].timestamp() > 0:
            _save_data.append(dict(time=offset['time'].timestamp(), x=offset['x'], y=offset['y'], z=offset['z']))
        elif isinstance(offset['time'], float) and offset['time'] > 0:
            _save_data.append(dict(time=offset['time'], x=offset['x'], y=offset['y'], z=offset['z']))
        elif isinstance(offset['time'], int) and offset['time'] > 0:
            _save_data.append(dict(time=offset['time'], x=offset['x'], y=offset['y'], z=offset['z']))
        else:
            logger.error(f'Unknown time format: {type(offset["time"])}')

    if len(_save_data) == 0:
        logger.error(f'No valid offset data to save for marker {marker_uri}')
        return False
    
    if not isinstance(_save_data[0]['time'], float):
        logger.error(f'Invalid time format: {type(_save_data[0]["time"])}')
        return False

    camera_id, marker_id = marker_uri.split('.')
    offset_data_dir = os.path.join("offsets", camera_id, marker_id)
    if not os.path.exists(offset_data_dir):
        os.makedirs(offset_data_dir)
    with open(os.path.join(offset_data_dir, 'offset.json'), 'w', encoding='utf-8') as f:
        json.dump(_save_data, f, ensure_ascii=False, indent=4)
    return True


def append_offset_data(marker_uri, offset_time, offset_x, offset_y, offset_z=0.0):
    """
    Append offset data to offset.json
    """
    logger.debug(f'Appending offset data for marker {marker_uri}')
    try:
        camera_id, marker_id = marker_uri.split('.')
        offset_data_dir = os.path.join("offsets", camera_id, marker_id)
        if not os.path.exists(offset_data_dir):
            os.makedirs(offset_data_dir)
        if not os.path.exists(os.path.join(offset_data_dir, 'offset.json')):
            with open(os.path.join(offset_data_dir, 'offset.json'), 'w', encoding='utf-8') as f:
                json.dump(dict(offsets=[]), f, ensure_ascii=False, indent=4)
        _offset_file = json.load(open(os.path.join(offset_data_dir, 'offset.json'), 'r', encoding='utf-8'))
        for offset in _offset_file['offsets']:
            offset['time'] = datetime.fromtimestamp(offset['time'])
        _offset_data = _offset_file['offsets']
        _offset_data.append(dict(time=offset_time, x=offset_x, y=offset_y, z=offset_z))
        save_offset_data(marker_uri, _offset_data)
        return True
    except:
        logger.error(f'Failed to append offset data for marker {marker_uri}')
        logger.error(traceback.format_exc())
        return False

