# server backend

import sys
import os
import time
import json
import shutil
from datetime import datetime, timedelta
import argparse
import threading
from flask import Flask, jsonify, request, render_template, redirect, url_for, send_from_directory, send_file
from flask_cors import CORS
import appfuncs as af
import cv2
import numpy as np
import ts_mono_calib as tsmcalib
from io import BytesIO

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

@app.route('/offset_plots/<string:camera_id>/<string:marker_id>', methods=['GET'])
def get_offset_plot(camera_id, marker_id):
    # send image file
    if not os.path.exists(f'offsets/{camera_id}/{marker_id}_offset.png'):
        return send_from_directory('webui/assets', 'no_data.png')
    return send_from_directory(f'offsets/{camera_id}', f'{marker_id}_offset.png?' + str(time.time()))

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
    data = {"frameurl": f"/get-camera-frame/{camera_id}.png?" + str(time.time())}
    return jsonify(status=1, data=data)


@app.route('/get-camera-frame/<string:camera_id>.png')
def get_camera_frame_jpg(camera_id):
    logger.debug(f'Getting frame for camera {camera_id}')
    if camera_id not in cam.cameras:
        return send_from_directory('webui/assets', 'noimage.png')
    frame = cam.get_frame(camera_id)
    if frame is None or len(frame) == 0:
        return send_from_directory('webui/assets', 'noimage.png')
    # encode to png
    imgdata = cv2.imencode('.png', frame)[1]#.tobytes()
    # Convert buffer to byte stream
    byte_io = BytesIO(imgdata)
    # Create a response using the byte stream
    return send_file(byte_io, mimetype='image/png')


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
            pst.settings['cameras'][cam_id] = dict(id=cam_id, name=cam.cameras[cam_id]['name'], ip=cam.cameras[cam_id]['ip'], settings=dict(x=0,y=0,z=0,pitch=0,roll=0,yaw=0,gain=0,exposure=1000), markers=dict())
        for k in req_data:
            if k == 'name':
                pst.settings['cameras'][cam_id]['name'] = req_data['name']
            elif k == 'ip':
                pst.settings['cameras'][cam_id]['ip'] = req_data['ip']
            elif k == 'id':
                pst.settings['cameras'][cam_id]['id'] = req_data['id']
            elif k == 'settings':
                for kk in req_data['settings']:
                    if kk in ['pitch', 'yaw', 'roll', 'x', 'y', 'z', 'gain', 'exposure']:
                        pst.settings['cameras'][cam_id]['settings'][kk] = float(req_data['settings'][kk])
                        if kk == 'exposure':
                            cam.set_camera_exposure(cam_id, float(req_data['settings'][kk]))
                        elif kk == 'gain':
                            cam.set_camera_gain(cam_id, float(req_data['settings'][kk]))
                    elif kk == 'standard':
                        pst.settings['cameras'][cam_id]['settings'][kk] = int(req_data['settings'][kk])
                    else:
                        pst.settings['cameras'][cam_id]['settings'][kk] = req_data['settings'][kk]
        pst.save_settings()
        print (pst.settings)
    return jsonify(status=1, data={})

@app.route('/api/v1/camera/calibrate', methods=['POST'])
def calibrate_camera():
    print (request.get_json())
    # {'id': 'K71601263', 'checkerboard': {'width': '3', 'height': '4', 'size': '0.05', 'images': 'd:\\calib'}}
    req_data = request.get_json()
    cam_id = req_data['id']
    if cam_id not in pst.settings['cameras']:
        return jsonify(status=0, data=dict(message="相机不存在"))
    if 'checkerboard' not in req_data:
        return jsonify(status=0, data=dict(message="缺少标定板参数"))
    ckbd = req_data['checkerboard']
    if 'width' not in ckbd or 'height' not in ckbd or 'size' not in ckbd or 'images' not in ckbd:
        return jsonify(status=0, data=dict(message="标定板参数不完整"))
    if not os.path.exists(ckbd['images']):
        return jsonify(status=0, data=dict(message="标定板图片路径不存在"))
    if not os.path.isdir(ckbd['images']):
        return jsonify(status=0, data=dict(message="标定板图片路径不是目录"))
    if len(os.listdir(ckbd['images'])) == 0:
        return jsonify(status=0, data=dict(message="标定板图片路径为空"))

    ckbd['width'] = int(ckbd['width'])
    ckbd['height'] = int(ckbd['height'])
    ckbd['size'] = float(ckbd['size'])
    ckbd['images'] = os.path.abspath(ckbd['images'])

    ret, (retVal, camMat, distMat, rvecs, tvecs) = tsmcalib.calibrate_mono_camera((ckbd['width'], ckbd['height']), ckbd['size'], ckbd['images'])

    if ret == 0:
        pst.settings['cameras'][cam_id]['intrinsics'] = camMat.tolist()
        pst.settings['cameras'][cam_id]['distortion'] = distMat.tolist()
        pst.save_settings()
        return jsonify(status=1)
    else:
        return jsonify(status=0)

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
    print (request.get_json())
    markers = request.get_json()['markers']
    if camera_id not in pst.settings['cameras']:
        print ("invalid camera id: ", camera_id, pst.settings['cameras'])
        return jsonify(status=0, data="invalid camera id")
    print (markers)
    pst.settings['cameras'][camera_id]['markers'] = dict()
    for marker in markers:
        pos = marker['position']
        rot = marker['rotation']
        roi = marker['roi']
        print (pos, rot, roi)
        if type(pos) is str:
            try:
                pos = [float(x) for x in str(pos).split(',')]
            except:
                pos = [0, 0, 0]
        if type(rot) is str:
            try:
                rot = [float(x) for x in str(rot).split(',')]
            except:
                rot = [0, 0, 0]
        if type(roi) is str:
            try:
                roi = [float(x) for x in str(roi).split(',')]
            except:
                roi = [0.001, 0.001, 0.999, 0.999]
        mk_obj = dict(
            id=marker['id'], 
            name=marker['name'], 
            type=marker['type'],
            position=pos,
            rotation=rot,
            size=float(marker['size']),
            roi=roi,
        )
        pst.settings['cameras'][camera_id]['markers'][marker['id']] = mk_obj
    pst.save_settings()
    return jsonify(status=1, data={})

@app.route('/api/v1/camera/capture-reference-image', methods=['POST'])
def capture_reference_image():
    # {'algorithm': 'elliptic', 'capture': '自动', 'frequency': '1000', 'sampleNumber': '20', 'save_path': 'd:/temp'}
    req = request.get_json()
    print (req)
    pst.settings['capture'] = dict(
        algorithm=req['algorithm'], 
        automate=bool(req['capture'] == "自动"), 
        interval=float(req['frequency']), 
        sampleNumber=int(req['sampleNumber']),
        running = False,
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    pst.save_settings()
    for camera_id in pst.settings['cameras']:
        camera_id_dir = os.path.join("offsets", str(camera_id))
        base_image_path = os.path.join(camera_id_dir, "base_image.bmp")
        if os.path.exists(base_image_path):
            os.unlink(base_image_path)
        target_image_path = os.path.join(camera_id_dir, "target_image.bmp")
        if os.path.exists(target_image_path):
            os.unlink(target_image_path)
        if os.path.exists(os.path.join(camera_id_dir, "check_log")):
            shutil.rmtree(os.path.join(camera_id_dir, "check_log"))
        os.makedirs(os.path.join(camera_id_dir, "check_log"))
        threading.Thread(target=af.get_image, args=(camera_id, base_image_path)).start()
        time.sleep(1)
    return jsonify(status=1, data={})
    

@app.route('/api/v1/camera/set-timed-check', methods=['POST'])
def set_timed_check():
    # Implement logic to set timed check
    if pst.settings['capture']['running'] == True:
        return jsonify(status=0, data=dict(message="检测已经在运行中"))
    else:
        pst.settings['capture']['running'] = True
        pst.save_settings()
        return jsonify(status=1, data={})


@app.route('/api/v1/camera/cancel-timed-check', methods=['POST'])
def cancel_timed_check():
    # Implement logic to cancel timed check
    if pst.settings['capture']['running'] == False:
        return jsonify(status=0, data=dict(message="检测没有在运行中"))
    else:
        pst.settings['capture']['running'] = False
        pst.save_settings()
        return jsonify(status=1, data={})


@app.route('/api/v1/camera/<string:camera_id>/get-timed-check-result', methods=['GET'])
def get_timed_check_result(camera_id):
    if camera_id not in pst.settings['cameras']:
        return jsonify(status=0, data=dict(message=f"相机{camera_id}不存在"))
    if pst.settings['capture']['running'] == False:
        return jsonify(status=0, data=dict(message="检测没有在运行中"))
    pst_cst = pst.settings['capture']['start_time']
    if pst_cst is None:
        return jsonify(status=0, data=dict(message="检测没有在运行中"))
    elif type(pst_cst) is str:
        cap_start_time = datetime.fromisoformat(pst_cst).timestamp()
        if cap_start_time > time.time():
            return jsonify(status=0, data=dict(message="检测没有在运行中"))
    elif type(pst_cst) in [int, float]:
        if pst_cst > time.time():
            return jsonify(status=0, data=dict(message="检测没有在运行中"))
    offsets = dict(
        camera=camera_id,
        algorithm=pst.settings['capture']['algorithm'],
        sample=pst.settings['capture']['sampleNumber'],
        interval=pst.settings['capture']['interval'],
        start_time=pst.settings['capture']['start_time'],
        results=[]
    )
    
    if not 'checkpoint_time' in af.checkpoint_data:
        return jsonify(status=0, data=dict(message="检测结果未准备好"))
    if not 'results' in af.checkpoint_data:
        return jsonify(status=0, data=dict(message="检测结果未准备好"))
    
    offsets['results'] = pst.load_offset_data(camera_id)
    # save to json
    json.dump(offsets, open(f"offsets_results.json", "w"))
    return jsonify(status=1, data=offsets)
    

@app.route('/api/v1/remote-server/set', methods=['POST'])
def set_remote_server():
    print (request.get_json())
    jdata = request.get_json()
    pst.settings['remote_server'] = dict(
        server1=jdata['server1'],
        server2=jdata['server2']
    )
    pst.save_settings()
    return jsonify(status=1, data={})

@app.route('/api/v1/remote-server/get', methods=['GET'])
def get_remote_server():
    servers = dict(
        server1=pst.settings['remote_server']['server1'],
        server2=pst.settings['remote_server']['server2']
    )
    return jsonify(status=1, data=servers)


if __name__ == '__main__':
    import uuid
    if not os.path.exists("offsets"):
        os.makedirs("offsets")

    if not os.path.exists("tmp"):
        os.makedirs("tmp")

    pst.load_settings()
    if "capture" not in pst.settings:
        pst.settings['capture'] = dict(
            algorithm="optical-flow", 
            automate=True, 
            interval=24, 
            sampleNumber=20,
            running = False,
            start_time = None
        )
    if "cameras" not in pst.settings:
        pst.settings['cameras'] = dict()
    if "remote_server" not in pst.settings:
        pst.settings['remote_server'] = dict(
            server1="", server2=""
        )
    if "machine" not in pst.settings:
        pst.settings['machine'] = dict(
            id=hex(uuid.getnode())[2:],
            name="biaoba_offset_box"
        )
    pst.save_settings()
    device_list, ret, deviceNum = cam.get_camera_list(return_json=True)
    print ("after get camera list")
    time.sleep(1)
    if deviceNum > 0:
        for device in device_list:
            if os.path.exists(os.path.join("offsets", device['id'])) is False:
                os.makedirs(os.path.join("offsets", device['id']))
            
            print ("load device: ", device)
            if device['id'] in pst.settings['cameras']:
                if device['ip'] == pst.settings['cameras'][device['id']]['ip']:
                    device.update(pst.settings['cameras'][device['id']])
                    device['new'] = 0
            if "settings" not in device:
                device['settings'] = {"exposure": 100000.0, "gain": 0, 
                                      "pitch": 0, "roll": 0, "yaw": 0, 
                                      "x": 0, "y": 0, "z": 0}
            threading.Thread(target=cam.ts_start_camera, args=(device['id'], device['settings']['exposure'], device['settings']['gain']), daemon=True).start()
            time.sleep(0.5)
    time.sleep(1)
    print ("wait for camera to start...")
    time.sleep(0.1)
    print ("start server...")
    app.run(host="0.0.0.0", port=5000, debug=False)
