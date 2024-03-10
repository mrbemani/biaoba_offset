# -*- coding: utf-8 -*-

__author__ = 'Shi Qi'

import sys
import os
import argparse
import json
import numpy as np
import cv2
from decimal import Decimal


def get_checkerboard_points(w, h, objp, images, imw=5472, winname="Camera Checkerboard View"):
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # camera 2d points in image plane.
    for fname in images:
        img = cv2.imread(fname)
        print (f"processing {fname} ...")
        ih, iw = img.shape[:2]
        nw = imw
        nh = int(float(ih) / float(iw) * float(nw))
        img = cv2.resize(img, (nw, nh))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (w,h), None)
        # If found, add object points, image points (after refining them)
        if ret is True:
            objpoints.append(objp)
            corners2=cv2.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
            ims = cv2.drawChessboardCorners(img, (w,h), corners2, ret)
            imgpoints.append(corners)
            ih, iw = ims.shape[:2]
            nw = 1280
            nh = int(float(ih) / float(iw) * float(nw))
            ims = cv2.resize(ims, (nw, nh))
            # Draw and display the corners
            cv2.imshow(winname, ims)
            k = cv2.waitKey(100)
            if k == 27:
                break
    return objpoints, imgpoints


def calibrate_mono_camera(cwh, cb_unit_size, camdir):
    w, h = cwh
    imgs = []
    if os.path.isdir(camdir):
        imgs = [os.path.join(camdir, p) for p in os.listdir(camdir) if p.lower().endswith('.jpg') or p.lower().endswith('.png') or p.lower().endswith('.bmp')]
    else:
        print ("[ERROR] camdir does not exist!")
        return (1, None)
    if len(imgs) < 2:
        print ("[ERROR] Images are empty.")
        return (2, None)
    imh, imw = cv2.imread(imgs[0]).shape[:2]
    imsize = (imw, imh)
    imgpoints = []
    objpoints = []
    objp = np.zeros((h*w,3), np.float32)
    objp[:,:2] = np.mgrid[0:w,0:h].T.reshape(-1,2) * cb_unit_size
    r = get_checkerboard_points(w, h, objp, imgs, imw)
    if r is not None:
        objpoints, imgpoints = r
    else:
        return (3, None)
    # camMatrix = np.zeros((3, 3), np.float32)
    # camMatrix[0,0] = 1.0
    # camMatrix[1,1] = 1.0
    camMatrix = cv2.initCameraMatrix2D(objpoints, imgpoints, imsize)
    print ("initial camMatrix: \n{}".format(camMatrix))
    camDist = np.zeros(8, dtype=np.float32)
    retval, camMatrix, camDist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, imsize, camMatrix, camDist, flags=0)
    #retval, camMatrix, camDist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, imsize, camMatrix, camDist, flags=flags)

    print ("===")
    print ("retval: {}".format(retval))
    print ("Intrinsics: {}".format(camMatrix))
    print ("Distortion: {}".format(camDist))
    print ("===")
    
    return (0, (retval, camMatrix, camDist, rvecs, tvecs))


def undistort_image(i_im, o_im, k, d):
    im = cv2.imread(i_im)
    ih, iw = im.shape[:2]
    # undistort
    dst = cv2.undistort(im, k, d, None, k)
    #dst = dst[y:y+h, x:x+w]
    cv2.imwrite(o_im, dst)




