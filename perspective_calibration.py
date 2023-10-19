# -*- coding: utf-8 -*-

__author__ = 'Shi Qi'

import sys
import os
import argparse
import json
from typing import Optional
from cv2 import perspectiveTransform
import numpy as np
import cv2
from decimal import Decimal
from gooey import Gooey

if getattr(sys, 'frozen', False):
    APP_BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
elif __file__:
    APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


#######################################################################################################################
# fix win10 scaling issue
if os.name == 'nt':
	import ctypes
	# Query DPI Awareness (Windows 10 and 8)
	awareness = ctypes.c_int()
	errorCode = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
	#print(awareness.value)

	# Set DPI Awareness  (Windows 10 and 8)
	errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)
	# the argument is the awareness level, which can be 0, 1 or 2:
	# for 1-to-1 pixel control I seem to need it to be non-zero (I'm using level 2)

	# Set DPI Awareness  (Windows 7 and Vista)
	success = ctypes.windll.user32.SetProcessDPIAware()
	# behaviour on later OSes is undefined, although when I run it on my Windows 10 machine, it seems to work with
	# effects identical to SetProcessDpiAwareness(1)
#######################################################################################################################


# CONSTANTS
KEY_ESC = 27
KEY_ENTER = 13
KEY_SPACE = 32
KEY_LT = 44
KEY_GT = 46
IMAGE_WIN = "Draw Window"

# VARIABLES
cursor_pos = (-1, -1)
fontpos = (8, 10)
fontsize = 28

# TEMPLATE RECTANGLE DIMS in Centimetre
tpl_x = 300
tpl_y = 400
DX = 1000
DY = 1000


######################################################
# chinese draw function
from PIL import Image, ImageDraw, ImageFont
def putTextPIL(cv2img, text, pt, fontsize=24, rgb=(0, 0, 0)):
    pilimg = Image.fromarray(cv2img)
    # PIL图片上打印汉字
    draw = ImageDraw.Draw(pilimg)
    font = ImageFont.truetype("simhei.ttf", fontsize, encoding="utf-8")
    draw.text(pt, text, rgb, font=font) # 参数1：打印坐标，参数2：文本，参数3：字体颜色，参数4：字体
    # PIL图片转cv 图片
    cv2charimg = cv2.cvtColor(np.array(pilimg), cv2.COLOR_RGB2BGR)
    return cv2charimg
######################################################


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def str2xmlfile(v):
    if v.lower().endswith(".xml"):
        if os.path.isfile(v):
            return v
    raise argparse.ArgumentTypeError('Invalid XML file path.')


def deci(n):
    return '%.16e' % Decimal(n)



# draw metric quad
def drawMetricQuad(frame: np.ndarray, pts: list = []) -> list:
    global cursor_pos
    pts = []
    if len(pts) > 0:
        cursor_pos = pts[-1]
    bDone = False
    def onMouseMetric(evt, x, y, flags, params):
        global cursor_pos
        cursor_pos = (x, y)
        if evt == cv2.EVENT_LBUTTONDOWN:
            if len(pts) <= 4:
                grayim = cv2.cvtColor(frame[y-10:y+10, x-10:x+10], cv2.COLOR_BGR2GRAY)
                corners = cv2.goodFeaturesToTrack(grayim, 25, 0.01, 10)
                corners = np.int0(corners)
                if len(corners) > 0:
                    dx, dy = corners[0].ravel()
                    pts.append((dx-10+x, dy-10+y))
        elif evt == cv2.EVENT_RBUTTONDOWN:
            if len(pts) > 0:
                del pts[-1]
    cv2.setMouseCallback(IMAGE_WIN, onMouseMetric, None)
    while bDone is False:
        k = cv2.waitKey(20) & 0xFF
        if k == KEY_ESC:
            pts = None
            return pts
        elif k == KEY_ENTER:
            bDone = True
        roi_frame = np.copy(frame)
        roi_frame = putTextPIL(roi_frame, "绘制地面一平方米方框 - [enter]: 完成, [esc]: 退出, [R-click]: 撤销", fontpos, fontsize, (255, 255, 0))
        if pts is not None and len(pts) > 0:
            if len(pts) == 1:
                cv2.line(roi_frame, tuple(pts[0]), tuple(cursor_pos), (255, 200, 200), 2)
            elif len(pts) < 4:
                for i, pt in enumerate(pts):
                    if i + 1 < len(pts):
                        cv2.line(roi_frame, tuple(pt), tuple(pts[i+1]), (255, 200, 200), 2)
                cv2.line(roi_frame, tuple(pts[-1]), tuple(cursor_pos), (255, 200, 200), 2)
                cv2.line(roi_frame, tuple(cursor_pos), tuple(pts[0]), (255, 200, 200), 2)
            else:
                for i, pt in enumerate(pts):
                    if i + 1 < len(pts):
                        cv2.line(roi_frame, tuple(pt), tuple(pts[i+1]), (255, 200, 200), 2)
                cv2.line(roi_frame, tuple(pts[-1]), tuple(pts[0]), (255, 200, 200), 2)
        cv2.imshow(IMAGE_WIN, roi_frame)
    return pts


def calib_main(imgfile):
    cv2.namedWindow(IMAGE_WIN)
    img = cv2.imread(imgfile)
    pts = []
    pts = drawMetricQuad(img, pts)
    #h, w = img.shape[:2]
    #pts = [[o[0] - w/2, o[1] - h/2] for o in pts]
    # [(1392, 554), (1489, 887), (1904, 868), (1747, 551)]
    tpl = np.float32([[DX, DY], [DX, DY+tpl_y], [DX+tpl_x, DY+tpl_y], [DX+tpl_x, DY]])
    pts = np.float32(pts)
    if len(pts) < 4:
        return False, None
    mat = cv2.getPerspectiveTransform(tpl, pts, cv2.DECOMP_LU)
    print (pts)
    print (mat)
    return True, mat


def check_main(mat, img):
    M = mat

    if img is None:
        print ("[ERROR] Input image invalid!")
        return 1
    
    cv2.namedWindow(IMAGE_WIN)
    warpimg = cv2.warpPerspective(img, np.linalg.inv(M), (3000, 2000))
    im = cv2.resize(warpimg, (1500, 1000))
    while True:
        cv2.imshow(IMAGE_WIN, im)
        k = cv2.waitKey(1)
        if k == 27: break
    cv2.imwrite("p_warp.png", warpimg)


def save_M(M: np.array, outfile: str = "P.xml"):
    cv_file = cv2.FileStorage(outfile, cv2.FILE_STORAGE_WRITE)
    cv_file.write("Perspective", M)
    cv_file.release()


@Gooey
def main():
    global tpl_x, tpl_y, DX, DY

    parser = argparse.ArgumentParser(description="Camera Perspective Matrix Calculation")
    parser.add_argument("-i", "--input_image", type=str, required=True, help="input image for calibration.")
    parser.add_argument("-x", "--rect_width", type=int, default=300, help="template rectangle width in CM.")
    parser.add_argument("-y", "--rect_height", type=int, default=400, help="template rectangle height in CM.")
    parser.add_argument("-u", "--rect_x", type=int, default=1000, help="template rectangle x in CM.")
    parser.add_argument("-v", "--rect_y", type=int, default=1000, help="template rectangle y in CM.")
    parser.add_argument("-s", "--save_xml_file", type=str, required=True, help="path to save xml file.")
    args = parser.parse_args()

    # M1 = [[ 9.79018943e-01, -2.51333927e-01,  9.81380525e+00],
    #       [ 1.20901717e-02,  3.60059956e-01,  2.33113845e+00],
    #       [ 5.65601681e-05, -2.92312686e-04,  1.00000000e+00]]

    tpl_x = args.rect_width
    tpl_y = args.rect_height
    DX = args.rect_x
    DY = args.rect_y
    
    ret, _M = calib_main(args.input_image)
    if ret is True:
        check_main(_M, cv2.imread(args.input_image))
        save_M(_M, args.save_xml_file)


if __name__ == '__main__':
    main()


