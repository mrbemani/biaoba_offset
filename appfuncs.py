

import os
import time
import cv2
import avgpixel
import tsutil as tsu
import persist as pst
import target as tg

try:
    import cam
except:
    print ("using fake camera!!!")
    import cam_mockup as cam


def get_image(camera_id, save_file, nPhoto=20):
    camdev = cam.cameras[camera_id]['deviceHandle']
    cam.nSaveNum = nPhoto
    cam.bSaveBmp = True
    cam.start_camera(camera_id, autoGrab=True)
    base_image_array = []
    while cam.bSaveBmp:
        time.sleep(1)
    for f in cam.savedFiles:
        im = cv2.imread(f, 0)
        base_image_array.append(im)
    fused_base_image = avgpixel.average_image_gray(base_image_array)
    cv2.imwrite(save_file, fused_base_image)
    cam.clear_saved_files(camera_id=camera_id)


def perform_comparison(camera_id, marker_id):
    marker_rect = pst.settings['cameras'][camera_id]['markers'][marker_id]['roi']
    base_image_file = os.path.join("offsets", str(camera_id), "base_image.bmp")
    base_image = cv2.imread(base_image_file, cv2.IMREAD_GRAYSCALE)
    if base_image is None:
        return None, False, "基准图像加载失败"
    # capture and save target_image
    target_image_file = os.path.join("offsets", str(camera_id), "target_image.bmp")
    get_image(target_image_file)
    target_image = cv2.imread(target_image_file, cv2.IMREAD_GRAYSCALE)
    if target_image is None:
        return None, False, "目标图像加载失败"
    # crop marker image for marker_id
    image_h, image_w = base_image.shape[:2]
    marker_rect = [marker_rect[0]*image_w, marker_rect[1]*image_h, marker_rect[2]*image_w, marker_rect[3]*image_h]
    base_marker_image = base_image[marker_rect[1]:marker_rect[1]+marker_rect[3], marker_rect[0]:marker_rect[0]+marker_rect[2]]
    target_marker_image = target_image[marker_rect[1]:marker_rect[1]+marker_rect[3], marker_rect[0]:marker_rect[0]+marker_rect[2]]
    # find marker ellipse
    ellipse, bbox = tsu.find_marker(base_marker_image)
    MARKER_DIAMETER = pst.settings['cameras'][camera_id]['markers'][marker_id]['size'] * 1000.0
    mmpp = MARKER_DIAMETER / max(ellipse[1][0], ellipse[1][1])
    x, y = tg.perform_compare(base_marker_image, target_marker_image)
    return x, y, mmpp


