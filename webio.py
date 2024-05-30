# use pywebio to setup camera and markers

import sys
import os
import time
import json
import traceback

import requests

import pywebio as pw
import pywebio.input as pwi
import pywebio.output as pwo

import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from uuid import uuid4

from persist import settings


try:
    import object_detector as odet
except:
    print ("Error: Can't import object_detector")
    print (traceback.format_exc())
    sys.exit(1)

yolo_model = odet.load_rknn_model("models/target_640.rknn")


def get_camera(idx=0):
    try:
        resp = requests.get('http://127.0.0.1:5000/api/v1/camera/list')
        if resp.status_code != 200:
            pw.error('无法连接到服务器')
            return None
        retjson = resp.json()
        if retjson['status'] != 1:
            pw.error('无法连接到服务器')
            return None
        cameras = retjson['data']['cameras']
        if len(cameras) == 0:
            pwo.put_error('没有找到相机')
            return None
        if idx >= len(cameras):
            pwo.put_error('相机索引错误')
            return None
        camera = cameras[idx]
        return camera
    except:
        print (traceback.format_exc())
        return None


def select_object_in_frame(frame, yolo_model, conf_thresh=0.01):
    _, boxes, classes, scores = odet.process_frame(frame, rknn_lite=yolo_model, augment_frame=False)
    h, w = frame.shape[0], frame.shape[1]
    if boxes is None:
        boxes = []
    if classes is None:
        classes = []
    if scores is None:
        scores = []
    obj_rects = []
    print (boxes, scores)
    for idx, b in enumerate(boxes):
        if scores[idx] < conf_thresh:
            print ("skip", scores[idx])
            continue
        xn, yn, wn, hn = (b[0] / w), (b[1] / h), ((b[2]-b[0]) / w), ((b[3]-b[1]) / h)
        if ((b[2]-b[0]) > 32 and (b[3]-b[1]) > 32) and wn / hn < 0.618 or hn / wn < 0.618:
            continue
        obj_rects.append([(xn, yn, wn, hn), scores[idx], classes[idx]])
    return obj_rects


def step_setup_camera():
    # setup camera
    pwo.put_info('设置相机')
    try:
        camera = get_camera()
        camera_id = camera['id']
        settings = {
          "exposure": 0.0,
          "gain": 0.0,
          "pitch": 0.0,
          "roll": 0.0,
          "standard": 0,
          "x": 0,
          "y": 0,
          "yaw": 0.0,
          "z": 0
        }
        if 'settings' in camera:
            settings.update(camera['settings'])
        form_camera = pwi.input_group("视频源", [
            pwi.input('相机ID', name="camera_id", value=camera_id, readonly=True),
            pwi.input('相机名称', name="camera_name", value=camera['name'], readonly=True),
            pwi.input('IP地址', name="ip", value=camera['ip'], readonly=True),
            pwi.input('曝光(0-200000, 0=自动)', name="exposure", type=pwi.NUMBER, value=settings['exposure'], readonly=False),
        ])

        camera_obj = {
            "id": camera_id, 
            "set": {
                "name": camera['name'], 
                "yaw": settings['yaw'],  
                "pitch": settings['pitch'], 
                "roll": settings['roll'], 
                "x": settings['x'],  
                "y": settings['y'], 
                "z": settings['z'], 
                "standard": settings['standard'], 
                "exposure": int(form_camera['exposure']), 
                "gain": settings['gain']
            }
        }

        if settings['exposure'] == int(form_camera['exposure']):
            pwo.put_info('相机设置不变')
            return

        resp = requests.post('http://127.0.0.1:5000/api/v1/camera/set', json=camera_obj)
        if resp.status_code != 200:
            pwo.put_error('设置相机失败')
            return
        retjson = resp.json()
        if retjson['status'] != 1:
            pwo.put_error('设置相机失败')
            return
        pwo.put_info('相机设置成功')
    except:
        print (traceback.format_exc())
        return


def step_prepare_markers():
    # setup markers
    pwo.put_info('设置标记')
    pwo.put_info('请确认标记在相机视野内, 且对焦清晰, 点击 "下一步" 开始自动搜索标记 ...')
    pwo.put_button('下一步', onclick=call_step_setup_markers)


def call_step_setup_markers():
    ret = step_setup_markers()
    if ret == 0:
        pwo.put_info('标记设置成功')
    elif ret == 1:
        pwo.clear()
        pwo.put_error('请确认相机已连接')
    elif ret == 2:
        pwo.clear()
        pwo.put_error('设置标记失败')
        pwo.put_button('重试', onclick=step_prepare_markers)
    else:
        pwo.clear()
        pwo.put_error('设置标记失败')


def step_setup_markers():  
    try:        
        camera = get_camera()
        if camera is None:
            pwo.put_info('没有找到相机')
            return 1
        pwo.put_info(f'加载相机 [{camera["id"]}] 预览...')
        camera_id = camera['id']
        cv_image = np.zeros((10, 10), np.uint8)
        while np.max(cv_image) < 30:
            resp = requests.get(f'http://127.0.0.1:5000/get-camera-frame/{camera["id"]}.png')
            if resp.status_code != 200:
                pwo.put_error('无法连接到服务器')
                return 2
            cv_image = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_GRAYSCALE)
            time.sleep(1)
        tl = (0, 0)
        br = (cv_image.shape[1] - 1, cv_image.shape[0] - 1)
        ims_h, ims_w = cv_image.shape[0], cv_image.shape[1]
        cv_image_nonzero = cv2.findNonZero(cv_image)
        if cv_image_nonzero is not None and len(cv_image_nonzero) > 0:
            x1 = np.min(cv_image_nonzero[:, 0, 0])
            y1 = np.min(cv_image_nonzero[:, 0, 1])
            x2 = np.max(cv_image_nonzero[:, 0, 0])
            y2 = np.max(cv_image_nonzero[:, 0, 1])
            tl = (x1, y1)
            br = (x2, y2)
        # pad 10 pixels around the marker
        tl = (max(0, tl[0] - 10), max(0, tl[1] - 10))
        br = (min(cv_image.shape[1] - 1, br[0] + 10), min(cv_image.shape[0] - 1, br[1] + 10))
        cropped_image = cv_image[tl[1]:br[1], tl[0]:br[0]]
        resize_ratio = 640 / cropped_image.shape[1]
        cropped_image = cv2.resize(cropped_image, (640, int(cropped_image.shape[0] * resize_ratio)))
        obj_rects = select_object_in_frame(cv2.cvtColor(cropped_image, cv2.COLOR_GRAY2BGR), yolo_model, conf_thresh=0.3)
        if len(obj_rects) == 0:
            pwo.put_error('没有找到标记')
            return 2
        print (tl, br, obj_rects)
        cv_rgbim = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2RGB)
        markers = []
        for idx, bbox in enumerate(obj_rects):
            (x, y, w, h), score, clsidx = bbox
            x1 = int(tl[0] + x * cropped_image.shape[1] / resize_ratio)
            y1 = int(tl[1] + y * cropped_image.shape[0] / resize_ratio)
            x2 = int(tl[0] + (x + w) * cropped_image.shape[1] / resize_ratio)
            y2 = int(tl[1] + (y + h) * cropped_image.shape[0] / resize_ratio)
            uuid4_str = uuid4().hex.replace('-', '').replace(':', '').lower()
            marker = dict(
                id = uuid4_str,
                name = 'marker_' + str(idx),
                type = 'circle',
                size = 100,
                roi = [(x1 - 2) / ims_w, (y1 - 2) / ims_h, (x2 + 4 - x1) / ims_w, (y2 + 4 - y1) / ims_h],
                position = [0, 0, 0],
                rotation = [0, 0, 0]
            )
            markers.append(marker)
            cv2.rectangle(cv_rgbim, (x1, y1), (x2, y2), (0, 255, 0), 8)
        pil_image = Image.fromarray(cv2.resize(cv_rgbim, (640, int(cv_rgbim.shape[0] * 640 / cv_rgbim.shape[1]))))
        pwo.put_image(pil_image)
        cv2.imwrite('markers_vis.png', cv_rgbim)
        pwo.put_info('标记设置中...')
        resp = requests.post(f'http://127.0.0.1:5000/api/v1/camera/{camera_id}/set-markers', json=dict(markers=markers))
        if resp.status_code != 200:
            pwo.put_error('标记设置失败')
            return 2
        retjson = resp.json()
        if retjson['status'] != 1:
            pwo.put_error('标记设置失败')
            return 2
        pwo.put_info('标记设置成功')
        return 0
    except:
        print (traceback.format_exc())
        return -1



def webui_init_task():
    form_compare_task = pwi.input_group('初始化对比任务', [
        pwi.input('对比间隔(分钟)', name='interval', type=pwi.NUMBER, placeholder='1440'),
        pwi.input('采样次数', name='sample_number', type=pwi.NUMBER, placeholder='5')
    ])
    try:
        postjson = {
            "algorithm": "optical-flow",
            "capture": "自动",
            "frequency": int(form_compare_task['interval']),
            "sampleNumber": int(form_compare_task['sample_number']),
        }
        resp = requests.post('http://127.0.0.1:5000/api/v1/camera/capture-reference-image', json=postjson)
        if resp.status_code != 200:
            pwo.put_error('初始化对比任务失败')
            return
        retjson = resp.json()
        if retjson['status'] != 1:
            pwo.put_error('初始化对比任务失败')
            return
        pwo.put_info('初始化对比任务成功 ... 正在启动对比 ... 请稍等 ...')
        time.sleep(5)
        resp = requests.post('http://127.0.0.1:5000/api/v1/camera/set-timed-check')
        if resp.status_code != 200:
            pwo.put_error('启动对比失败')
            return
        retjson = resp.json()
        if retjson['status'] != 1:
            pwo.put_error('启动对比失败')
            return
        time.sleep(5)
        pwo.put_info('对比已启动, 可以关闭此页面')
        pwo.put_button('返回首页查看对比结果', onclick=webui)
    except:
        print (traceback.format_exc())
        pwo.put_error('初始化对比任务失败')
        pwo.put_error(traceback.format_exc())

        
def webui_stop_task():
    try:
        resp = requests.post('http://127.0.0.1:5000/api/v1/camera/cancel-timed-check')
        if resp.status_code != 200:
            pwo.put_error('停止对比任务失败')
            return
        retjson = resp.json()
        if retjson['status'] != 1:
            pwo.put_error('停止对比任务失败')
            return
        pwo.put_info('停止对比任务成功')
        time.sleep(2)
        webui()
    except:
        print (traceback.format_exc())
        pwo.put_error('停止对比任务失败')
        pwo.put_error(traceback.format_exc())


def is_camera_set():
    cam_is_set = False
    camera = None
    if 'cameras' in settings and len(settings['cameras']) > 0:
        print (settings['cameras'])
        for cam_id in settings['cameras']:
            camera = settings['cameras'][cam_id]
            break
        if 'markers' in camera and len(camera['markers']) > 0:
            cam_is_set = True
            pwo.put_info('相机已设置')
    return cam_is_set, camera


def get_offset_results(cam_id):
    results = None
    try:
        resp = requests.get(f"http://127.0.0.1:5000/api/v1/camera/{cam_id}/get-timed-check-result")
        if resp.status_code != 200:
            return None
        retjson = resp.json()
        if retjson['status'] != 1:
            return None
        results = retjson['data']['results']
    except:
        print (traceback.format_exc())
    return results


def webui_device_reboot():
    pwo.clear()
    pwo.put_info('设备正在重启 ... 请稍等 ...')
    # show an 120 seconds countdown
    pwo.put_html('<div id="countdown">120</div>')
    pwo.put_html('<script>var countdown = 120; setInterval(function() { countdown--; document.getElementById("countdown").innerText = countdown; if (countdown == 0) { window.location.reload(); } }, 1000);</script>')
    time.sleep(5)
    os.system('sudo reboot')


def webui():
    pwo.put_info('请稍等 ... ')
    cam_is_set, camera = is_camera_set()
    camera_id = None
    if cam_is_set is True:
        camera_id = camera['id']
    pwo.clear()

    task_is_running = False
    if cam_is_set and camera is not None:
        if 'capture' in settings and settings['capture']['running'] is True:
            task_is_running = True
            results = get_offset_results(camera_id)
            if type(results) is not None:
                # plots = []
                for marker_id in camera['markers']:
                    pwo.put_image(f'/offset_plots/{camera_id}/{marker_id}?{time.time()}')
                pwo.put_file('下载对比结果', json.dumps(results), f'{camera_id}.json')
        else:
            task_is_running = False
    
    pwo.put_markdown('### 安装设置')
    pwo.put_button('设置相机与标靶', onclick=webui_setup)
    
    if cam_is_set:
        pwo.put_markdown('### 对比任务')
        if task_is_running:
            pwo.put_button('停止对比任务', onclick=webui_stop_task)
        else:
            pwo.put_button('初始化对比任务', onclick=webui_init_task)
    
    pwo.put_markdown('### 设备控制')
    pwo.put_button('重启设备', onclick=webui_device_reboot)


def webui_setup():
    pwo.clear()
    step_setup_camera()
    pwo.clear()
    step_prepare_markers()