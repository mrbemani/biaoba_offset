# server backend

import sys
import os
import time
import argparse
import threading
from flask import Flask, jsonify, request, render_template, redirect, url_for, send_from_directory
from flask_cors import CORS
import appfuncs as af

try:
    import cam
except:
    print ("using fake camera!!!")
    import cam_mockup as cam

from ts_logger import logger
import persist as pst

app = Flask(__name__)
CORS(app)

SYS_TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
# get system temp dir
if not os.path.exists(SYS_TEMP_DIR):
    os.makedirs(SYS_TEMP_DIR)


@app.route('/debug/get/settings', methods=['GET'])
def debug_get_settings():
    return jsonify(status=1, data=pst.settings)


@app.route('/', methods=['GET'])
def index():
    return send_from_directory('webui', 'index.html')

@app.route('/assets/<path:path>', methods=['GET'])
def send_assets(path):
    return send_from_directory('webui/assets', path)

@app.route('/api/v1/camera/list', methods=['GET'])
def get_camera_list():
    logger.debug('Getting camera list')
    cameras, ret, num_devices = cam.get_camera_list(return_json=True) 
    if not ret:
        return jsonify(status=0, data={"cameras": []})
    if num_devices == 0:
        return jsonify(status=1, data={"cameras": []})
    logger.debug(f'Found {num_devices} camera(s)')
    for camera in cameras:
        camera['name'] = f'New Camera {camera["id"]}' if 'name' not in camera else camera['name']
        camera['ip'] = None if 'ip' not in camera else camera['ip']
        camera['settings'] = {} if 'settings' not in camera else camera['settings']
        camera['intrinsics'] = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0] if 'intrinsics' not in camera else camera['intrinsics']
        camera['distortion'] = [1.0, 0.0, 0.0, 0.0, 0.0] if 'distortion' not in camera else camera['distortion']
        camera['new'] = 1
        if camera['id'] in pst.settings['cameras']:
            if camera['ip'] == pst.settings['cameras'][camera['id']]['ip']:
                camera.update(pst.settings['cameras'][camera['id']])
                camera['new'] = 0
            
    return jsonify(status=1, data={"cameras": cameras})

@app.route('/api/v1/camera/<string:camera_id>/get-frame', methods=['GET'])
def get_camera_frame(camera_id):
    # Implement logic to return the camera frame
    data = {"frameurl": f"/get-camera-frame/{camera_id}.bmp"}
    return jsonify(status=1, data=data)


@app.route('/get-camera-frame/<string:camera_id>.bmp')
def get_camera_frame_jpg(camera_id):
    logger.debug(f'Getting frame for camera {camera_id}')
    return send_from_directory('frames', f'{camera_id}.bmp')


@app.route('/api/v1/camera/<string:camera_id>/get-info', methods=['GET'])
def get_camera_info(camera_id):
    # Implement logic to return camera info
    logger.debug(f'Getting info for camera {camera_id}')
    cam_info = dict(id=camera_id, name="", ip="", settings=[], intrinsics=[], distortion=[])
    if camera_id in pst.settings['cameras']:
        cam_info.update(pst.settings['cameras'][camera_id])
    if "markers" in cam_info:
        del cam_info["markers"]
    return jsonify(status=1, data=cam_info)


@app.route('/api/v1/camera/set', methods=['POST'])
def set_camera():
    print (request.get_json())
    req_data = request.get_json()
    logger.debug(f'Setting camera {req_data["id"]}')
    cam_id = req_data['id']
    logger.debug(f'req_data: \n{req_data}')
    if 'settings' in req_data:
        if cam_id not in pst.settings['cameras']:
            pst.settings['cameras'][cam_id] = dict(settings=dict())
        for k in req_data['settings']:
            if k == 'name':
                pst.settings['cameras'][cam_id]['name'] = req_data['settings']['name']
            else:
                if k in ['pitch', 'yaw', 'roll', 'x', 'y', 'z', 'gain', 'exposure']:
                    pst.settings['cameras'][cam_id]['settings'][k] = float(req_data['settings'][k])
                    if k == 'exposure':
                        cam.set_camera_exposure(cam_id, float(req_data['settings'][k]))
                    elif k == 'gain':
                        cam.set_camera_gain(cam_id, float(req_data['settings'][k]))
                elif k == 'standard':
                    pst.settings['cameras'][cam_id]['settings'][k] = int(req_data['settings'][k])
                else:
                    pst.settings['cameras'][cam_id]['settings'][k] = req_data['settings'][k]
        pst.save_settings()
        print (pst.settings)
    return jsonify(status=1, data={})

@app.route('/api/v1/camera/calibrate', methods=['POST'])
def calibrate_camera():
    print (request.get_json())
    return jsonify(status=1, data={})

@app.route('/api/v1/camera/<string:camera_id>/list-markers', methods=['GET'])
def list_markers(camera_id):
    if camera_id not in pst.settings['cameras']:
        return jsonify(status=0, data={"markers": []})
    if 'markers' not in pst.settings['cameras'][camera_id]:
        pst.settings['cameras'][camera_id]['markers'] = []
        pst.save_settings()
    ret_markers = []
    for marker in pst.settings['cameras'][camera_id]['markers']:
        ret_markers.append(pst.settings['cameras'][camera_id]['markers'][marker])
    return jsonify(status=1, data={"markers": ret_markers})

@app.route('/api/v1/camera/<string:camera_id>/set-markers', methods=['POST'])
def set_markers(camera_id):
    if 'markers' not in request.get_json():
        return jsonify(status=0, data="invalid request")
    markers = request.get_json()['markers']
    if camera_id not in pst.settings['cameras']:
        return jsonify(status=0, data="invalid camera id")
    pst.settings['cameras'][camera_id]['markers'] = dict()
    for marker in markers:
        mk_obj = dict(
            id=marker['id'], 
            name=marker['name'], 
            type=marker['type'],
            position=[float(x) for x in marker['position'].split(',')],
            rotation=[float(x) for x in marker['rotation'].split(',')],
            size=float(marker['size']),
            roi=[float(x) for x in marker['roi'].split(',')],
        )
        pst.settings['cameras'][camera_id]['markers'][marker['id']] = mk_obj
    pst.save_settings()
    return jsonify(status=1, data={})

@app.route('/api/v1/camera/capture-reference-image', methods=['POST'])
def capture_reference_image():
    req = request.get_json()
    print (req)
    sample_num = 20
    if 'id' not in req:
        return jsonify(status=0, data="invalid request")
    save_path = os.path.join(SYS_TEMP_DIR, "capture", "reference", str(req['id']).strip().replace("-", "_").replace("/", "_"))
    camera_id = req['id']
    if camera_id not in pst.settings['cameras']:
        return jsonify(status=0, data="invalid camera id")
    if 'sampleNumber' in req:
        sample_num = int(req['sampleNumber'])
    af.get_image(os.path.join("offsets", str(camera_id), "base_image.bmp"), sample_num)
    return jsonify(status=1, data={})
    

@app.route('/api/v1/camera/check-offset', methods=['POST'])
def check_offset():
    # Implement logic to check offset

    
    pass

@app.route('/api/v1/camera/set-timed-check', methods=['POST'])
def set_timed_check():
    # Implement logic to set timed check
    pass

@app.route('/api/v1/camera/cancel-timed-check', methods=['POST'])
def cancel_timed_check():
    # Implement logic to cancel timed check
    pass

@app.route('/api/v1/camera/<string:camera_id>/get-timed-check', methods=['GET'])
def get_timed_check(camera_id):
    # Implement logic to get timed check status
    pass

@app.route('/api/v1/camera/<string:camera_id>/get-timed-check-result', methods=['GET'])
def get_timed_check_result(camera_id):
    pst.load_offset_data(camera_id)
    

@app.route('/api/v1/remote-server/set', methods=['POST'])
def set_remote_server():
    pst.settings['remote_server'] = request.get_json()
    return jsonify(status=1, data={})

@app.route('/api/v1/remote-server/get', methods=['GET'])
def get_remote_server():
    return jsonify(status=1, data=pst.settings['remote_server'])

if __name__ == '__main__':
    pst.load_settings()
    device_list, ret, deviceNum = cam.get_camera_list(return_json=True)
    print ("after get camera list")
    time.sleep(1)
    if deviceNum > 0:
        for device in device_list:
            print ("load device: ", device)
            if device['id'] in pst.settings['cameras']:
                if device['ip'] == pst.settings['cameras'][device['id']]['ip']:
                    device.update(pst.settings['cameras'][device['id']])
                    device['new'] = 0
            if "settings" not in device:
                device['settings'] = {"exposure": 1000.0, "gain": 0, 
                                      "pitch": 0, "roll": 0, "yaw": 0, 
                                      "x": 0, "y": 0, "z": 0}
            threading.Thread(target=cam.ts_start_camera, args=(device['id'], device['settings']['exposure']), daemon=True).start()
            time.sleep(0.5)
    time.sleep(3)
    app.run(debug=True)
