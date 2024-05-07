

import os
import time
from datetime import datetime
import traceback
import requests
import cv2
import numpy as np
import matplotlib.pyplot as plt
import avgpixel
import threading
import tsutil as tsu
import persist as pst
import target as tg

# config log to file
import logging
tslogger = logging.getLogger('app_logger')
tslogger.setLevel(logging.DEBUG)
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
tslogger.addHandler(fh)





try:
    import cam
except:
    print ("Failed to import camera!!!")
    exit(1)

from queue import Queue


worker = None
deinit = False
checkpoint_data = dict()

"""
{
  "checkpoint_time": "2020-05-01 12:00:00",  // 检测时间
  "reference_time": "2020-01-01 12:00:00",   // 参照时间
  "results": [
    {   
        "camera_id": "002345033344",      // 相机ID
        "marker_id": "1234567890",        // 标靶ID
        "dx": 1.0,                         // 位移x (mm)
        "dy": 2.0,                         // 位移y (mm)
    },
    {
        "camera_id": "002345033344",
        "marker_id": "1234567891",
        "dx": 1.0,
        "dy": 2.0
    },
    //...
  ]
}
"""
def submit_checkpoint(checkpoint_data):
    # reformat checkpoint_data
    cpdfmt = dict()
    cpdfmt['reference_time'] = pst.settings['capture']['start_time']
    cpdfmt['results'] = []
    for camera_id in checkpoint_data:
        for marker_id in checkpoint_data[camera_id]:
            x = checkpoint_data[camera_id][marker_id]['x']
            y = checkpoint_data[camera_id][marker_id]['y']
            mmpp = checkpoint_data[camera_id][marker_id]['mmpp']
            cpdfmt['results'].append(dict(camera_id=camera_id, 
                                          marker_id=marker_id, 
                                          dx=x*mmpp, 
                                          dy=y*mmpp))
    cpdfmt['checkpoint_time'] = datetime.now().isoformat()
    # submit checkpoint_data to server1 and server2 if available
    try:
        if 'server1' in pst.settings['remote_server']:
            url = pst.settings['remote_server']['server1']
            if not url.startswith("http://"):
                return
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=cpdfmt, headers=headers, timeout=10)
            if response.status_code != 200:
                tslogger.warning(f"Failed to submit checkpoint data to server1: {response.status_code}")
                print (f"Failed to submit checkpoint data to server1: {response.status_code}")
        if 'server2' in pst.settings['remote_server']:
            url = pst.settings['remote_server']['server2']
            if not url.startswith("http://"):
                return
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=cpdfmt, headers=headers, timeout=10)
            if response.status_code != 200:
                tslogger.warning(f"Failed to submit checkpoint data to server2: {response.status_code}")
                print (f"Failed to submit checkpoint data to server2: {response.status_code}")
    except:
        tslogger.error("Failed to submit checkpoint data")
        tslogger.error(traceback.format_exc())
        print ("Failed to submit checkpoint data")
        print (traceback.format_exc())
            

def plot_offsets(camera_id):
    # draw offsets of a camera
    offsets = pst.load_offset_data(camera_id)
    # draw each marker's offsets in a figure
    for marker_id in offsets:
        plt.figure()
        # plot line chart
        plt.plot(
            offsets[marker_id]['time'],
            np.float32(offsets[marker_id]['x']) * np.float32(offsets[marker_id]['mmpp']), 
            marker='o', linestyle='-', color='b'
        )
        plt.plot(
            offsets[marker_id]['time'],
            np.float32(offsets[marker_id]['y']) * np.float32(offsets[marker_id]['mmpp']), 
            marker='o', linestyle='-', color='r'
        )        
        plt.xlabel('datetime')
        plt.ylabel('x, y (mm)')
        plt.title(f'Camera {camera_id} Marker {marker_id} Offsets')
        plt.grid()
        # save figure
        plt.savefig(f'offsets/{camera_id}/{marker_id}_offset.png')


def get_image(camera_id, save_file):
    camobj = cam.cameras[camera_id]
    camdev = camobj['deviceHandle']
    cam.nSaveNum = 10
    camobj['bSave'] = True
    #cam.start_camera(camera_id, autoGrab=True)
    cam.clear_saved_files(camera_id=camera_id)
    base_image_array = []
    while len(cam.cameras[camera_id]['savedFiles']) < 10:
        time.sleep(1)
    for f in cam.cameras[camera_id]['savedFiles']:
        im = cv2.imread(f, 0)
        base_image_array.append(im)
    fused_base_image = avgpixel.average_image_gray(base_image_array)
    cv2.imwrite(save_file, fused_base_image)
    cam.clear_saved_files(camera_id=camera_id)
    camobj['bSave'] = False


def perform_comparison(camera_id):
    # capture and save target_image
    target_image_file = os.path.join("offsets", str(camera_id), "target_image.bmp")
    get_image(camera_id, target_image_file)
    target_image = cv2.imread(target_image_file, cv2.IMREAD_GRAYSCALE)
    if target_image is None:
        return None, False, "目标图像加载失败"

    base_image_file = os.path.join("offsets", str(camera_id), "base_image.bmp")
    base_image = cv2.imread(base_image_file, cv2.IMREAD_GRAYSCALE)
    if base_image is None:
        return None, False, "基准图像加载失败"
    offsets = dict()
    for marker_id in pst.settings['cameras'][camera_id]['markers']:
        marker_roi = pst.settings['cameras'][camera_id]['markers'][marker_id]['roi']
        h, w = target_image.shape[:2]
        marker_crop = [int(marker_roi[0]*w), int(marker_roi[1]*h), int(marker_roi[2]*w), int(marker_roi[3]*h)]
        t_roi = target_image[marker_crop[1]:marker_crop[1]+marker_crop[3], marker_crop[0]:marker_crop[0]+marker_crop[2]]
        b_roi = base_image[marker_crop[1]:marker_crop[1]+marker_crop[3], marker_crop[0]:marker_crop[0]+marker_crop[2]]
        MARKER_DIAMETER = pst.settings['cameras'][camera_id]['markers'][marker_id]['size']
        x, y, mmpp = compare_marker(b_roi, t_roi, MARKER_DIAMETER)
        if x is not None and y is not None and mmpp is not None:
            offsets[marker_id] = dict(x=x, y=y, mmpp=mmpp, time=datetime.now().isoformat())
    return offsets, True, "Success"


def compare_marker(base_marker_image, target_marker_image, MARKER_DIAMETER):
    # find marker ellipse
    ellipse, bbox = tsu.find_marker(base_marker_image)
    mmpp = MARKER_DIAMETER / max(ellipse[1][0], ellipse[1][1])
    x, y = tg.perform_compare(base_marker_image, target_marker_image)
    return x, y, mmpp


def capture_check_thread():
    while True:
        if deinit is True:
            break
        if type(pst.settings) is not dict:
            time.sleep(5)
            continue
        if 'cameras' not in pst.settings or len(pst.settings['cameras']) == 0:
            time.sleep(5)
            continue
        if 'capture' not in pst.settings or not pst.settings['capture']:
            time.sleep(5)
            continue
        if pst.settings['capture']['running'] == False:
            time.sleep(5)
            continue
        if pst.settings['capture']['start_time'] is None:
            time.sleep(5)
            continue
        try:
            capture_start_timestamp = datetime.strptime(pst.settings['capture']['start_time'], "%Y-%m-%d %H:%M:%S").timestamp()
            if capture_start_timestamp > time.time():
                time.sleep(5)
                continue
        except:
            time.sleep(5)
            continue
        try:
            not_ready = False
            for camera_id in pst.settings['cameras']:
                if camera_id not in cam.cameras:
                    not_ready = True
                    continue
                if 'markers' not in pst.settings['cameras'][camera_id]:
                    not_ready = True
                    continue
                if len(pst.settings['cameras'][camera_id]['markers']) == 0:
                    not_ready = True
                    continue
                if not os.path.exists(os.path.join("offsets", str(camera_id))):
                    os.makedirs(os.path.join("offsets", str(camera_id)))
                base_image_file = os.path.join("offsets", str(camera_id), "base_image.bmp")
                if not os.path.exists(base_image_file):
                    not_ready = True
            if not not_ready:
                checkpoint_data.clear()
                for camera_id in pst.settings['cameras']:
                    # perform comparison for each marker in each camera and save offsets
                    sampleNumber = int(pst.settings['capture']['sampleNumber']) or 1
                    compareSamples = []
                    # capture and compare target with base image
                    for i in range(sampleNumber):
                        offsets, success, message = perform_comparison(camera_id)
                        if success and offsets is not None:
                            # save offsets in compareSamples
                            compareSamples.append(offsets)
                            print ("Successfully performed compare marker for camera %s" % camera_id)
                        else:
                            break
                    # check if all samples are valid
                    if len(compareSamples) == 0:
                        print (f"Failed to compare marker for camera {camera_id}: {message}")
                        break
                    # perform average
                    offsets = dict()
                    for marker_id in compareSamples[0]:
                        x = 0.0
                        y = 0.0
                        mmpp = 0.0
                        for i in range(len(compareSamples)):
                            x += compareSamples[i][marker_id]['x']
                            y += compareSamples[i][marker_id]['y']
                            mmpp += compareSamples[i][marker_id]['mmpp']
                        x /= len(compareSamples)
                        y /= len(compareSamples)
                        mmpp /= len(compareSamples)
                        offsets[marker_id] = dict(x=x, y=y, mmpp=mmpp, time=datetime.now().isoformat())
                        print ("averaged result for camera %s marker %s" % (camera_id, marker_id))
                    # save averaged offsets
                    if success:
                        print (f"Success to compare marker for camera {camera_id}")
                        for marker_id in offsets:
                            pst.save_offset_data(camera_id, marker_id, offsets[marker_id])
                        checkpoint_data[camera_id] = offsets
                        plot_offsets(camera_id)
                    else:
                        print (f"Failed to compare marker for camera {camera_id}: {message}")
                        break
                if len(checkpoint_data) > 0:
                    try:
                        submit_checkpoint(checkpoint_data)
                    except:
                        tslogger.error("Failed to submit checkpoint data")
                        tslogger.error(traceback.format_exc())
                        print ("Failed to submit checkpoint data")
                        print (traceback.format_exc())
            time.sleep(60*pst.settings['capture']['interval'])
        except:
            tslogger.error("Failed to perform comparison")
            tslogger.error(traceback.format_exc())
            print ("Failed to perform comparison")
            print (traceback.format_exc())
            time.sleep(10)


def appfuncs_deinit():
    global worker, deinit
    deinit = True
    if worker is not None:
        worker.join()
        worker = None

import atexit
atexit.register(appfuncs_deinit)

worker = threading.Thread(target=capture_check_thread)
worker.daemon = True
worker.start()


