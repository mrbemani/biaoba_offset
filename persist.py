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


def load_offset_data(camera_id):
    """
    Load offset data from disk
    """
    logger.debug(f'Loading offset data for camera {camera_id}')
    offset_data_dir = os.path.join("offsets", camera_id, "check_log")
    try:
        if not os.path.exists(offset_data_dir):
            os.makedirs(offset_data_dir)
        offset_data = {}
        for marker_file in os.listdir(offset_data_dir):
            with open(os.path.join(offset_data_dir, marker_file), 'r', encoding='utf-8') as f:
                f_lines = f.readlines()
                marker_id = marker_file.split('.')[0]
                offset_data[marker_id] = dict()
                offset_data[marker_id]['time'] = []
                offset_data[marker_id]['mmpp'] = []
                offset_data[marker_id]['x'] = []
                offset_data[marker_id]['y'] = []
                for line in f_lines:
                    line_data = line.split('||')
                    offset_data[marker_id]['time'].append(line_data[0])
                    offset_data[marker_id]['mmpp'].append(float(line_data[1]))
                    offset_data[marker_id]['x'].append(float(line_data[2]))
                    offset_data[marker_id]['y'].append(float(line_data[3]))
        return offset_data
    except:
        logger.error(f'Failed to load offset data for camera {camera_id}')
        logger.error(traceback.format_exc())
        return None
    

def get_offset_images():
    """
    Get offset images
    """
    logger.debug('Getting offset images')
    try:
        offset_images = []
        for camera_id in settings['cameras']:
            for marker_id in settings['cameras'][camera_id]['markers']:
                marker_offset_image = os.path.join("offsets", camera_id, marker_id + "_offset.png")
                if os.path.exists(marker_offset_image):
                    offset_images.append(marker_offset_image)
        return offset_images
    except:
        logger.error('Failed to get offset images')
        logger.error(traceback.format_exc())
        return None