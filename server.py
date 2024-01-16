# server backend

import sys
import os
import argparse
import threading
from flask import Flask, jsonify, request, render_template, redirect, url_for, send_from_directory
from flask_cors import CORS
import cam


app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def index():
    return send_from_directory('webui', 'index.html')

@app.route('/assets/<path:path>', methods=['GET'])
def send_assets(path):
    return send_from_directory('webui/assets', path)

@app.route('/api/v1/camera/list', methods=['GET'])
def get_camera_list():
    cameras, ret, num_devices = cam.get_camera_list(return_json=True)
    if not ret:
        return jsonify(status=0, data={"cameras": []})
    if num_devices == 0:
        return jsonify(status=1, data={"cameras": []})
    print (cameras)
    return jsonify(status=1, data={"cameras": cameras})

@app.route('/api/v1/camera/<int:camera_id>/get-frame', methods=['GET'])
def get_camera_frame(camera_id):
    # Implement logic to return the camera frame
    pass

@app.route('/api/v1/camera/<int:camera_id>/get-info', methods=['GET'])
def get_camera_info(camera_id):
    # Implement logic to return camera info
    pass

@app.route('/api/v1/camera/set', methods=['POST'])
def set_camera():
    # Implement logic to set camera parameters
    pass

@app.route('/api/v1/camera/calibrate', methods=['POST'])
def calibrate_camera():
    # Implement logic for camera calibration
    pass

@app.route('/api/v1/camera/<int:camera_id>/list-markers', methods=['GET'])
def list_markers(camera_id):
    # Implement logic to list markers
    pass

@app.route('/api/v1/camera/<int:camera_id>/set-markers', methods=['POST'])
def set_markers(camera_id):
    # Implement logic to set markers
    pass

@app.route('/api/v1/camera/capture-reference-image', methods=['POST'])
def capture_reference_image():
    # Implement logic for capturing reference image
    pass

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

@app.route('/api/v1/camera/<int:camera_id>/get-timed-check', methods=['GET'])
def get_timed_check(camera_id):
    # Implement logic to get timed check status
    pass

@app.route('/api/v1/camera/<int:camera_id>/get-timed-check-result', methods=['GET'])
def get_timed_check_result(camera_id):
    # Implement logic to get timed check results
    pass

@app.route('/api/v1/remote-server/set', methods=['POST'])
def set_remote_server():
    # Implement logic to set remote server
    pass

@app.route('/api/v1/remote-server/get', methods=['GET'])
def get_remote_server():
    # Implement logic to get remote server info
    pass

if __name__ == '__main__':
    threading.Thread(target=cam.ts_start_camera, args=(0, 5000.0), daemon=True).start()
    app.run(debug=True)
