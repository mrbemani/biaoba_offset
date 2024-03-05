

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
    print ("Failed to import camera!!!")
    exit(1)


def get_image(camera_id, save_file, nPhoto=20):
    camdev = cam.cameras[camera_id]['deviceHandle']
    cam.nSaveNum = nPhoto
    cam.bSaveBmp = True
    #cam.start_camera(camera_id, autoGrab=True)
    cam.clear_saved_files(camera_id=camera_id)
    base_image_array = []
    while cam.cameras[camera_id]['savedFiles'] < nPhoto:
        time.sleep(1)
    for f in cam.cameras[camera_id]['savedFiles']:
        im = cv2.imread(f, 0)
        base_image_array.append(im)
    fused_base_image = avgpixel.average_image_gray(base_image_array)
    cv2.imwrite(save_file, fused_base_image)
    cam.clear_saved_files(camera_id=camera_id)


def perform_comparison(camera_id):
    # capture and save target_image
    target_image_file = os.path.join("offsets", str(camera_id), "target_image.bmp")
    get_image(camera_id, target_image_file, nPhoto=20)
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
        MARKER_DIAMETER = pst.settings['cameras'][camera_id]['markers'][marker_id]['size'] * 1000.0
        x, y, mmpp = compare_marker(b_roi, t_roi, MARKER_DIAMETER)
        if x is not None and y is not None and mmpp is not None:
            offsets[marker_id] = dict(x=x, y=y, mmpp=mmpp)
    return offsets, True, "Success"


def compare_marker(base_marker_image, target_marker_image, MARKER_DIAMETER):
    # find marker ellipse
    ellipse, bbox = tsu.find_marker(base_marker_image)
    mmpp = MARKER_DIAMETER / max(ellipse[1][0], ellipse[1][1])
    x, y = tg.perform_compare(base_marker_image, target_marker_image)
    return x, y, mmpp


